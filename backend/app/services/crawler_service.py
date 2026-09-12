"""
Synchronization and scheduling for external crawlers.
"""

from __future__ import annotations

import asyncio
import uuid
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Optional

import redis.asyncio as redis
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import settings
from app.database import AsyncSessionLocal
from app.models.resource import Resource
from app.models.site_settings import SiteSetting
from app.services.crawlers.source_1024 import (
    CRAWLER_FIELD_OPTIONS,
    ExternalResourceCandidate,
    Source1024Crawler,
)
from app.services.site_settings import get_1024_crawler_settings, upsert_setting
from app.utils.datetime_utils import utc_now
from app.utils.logging import get_logger
from app.utils.seo import generate_slug


logger = get_logger(__name__)


class CrawlerAlreadyRunningError(RuntimeError):
    """Raised when another local or distributed crawler run owns the lease."""


class CrawlerCoordinationUnavailableError(RuntimeError):
    """Raised when the distributed crawler lease cannot be checked safely."""


class CrawlerLeaseLostError(CrawlerCoordinationUnavailableError):
    """Raised when a run no longer owns its distributed lease."""


def _create_crawler_redis_client() -> Any:
    """Create a short-timeout Redis client dedicated to crawler coordination."""
    return redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3,
    )


async def _safe_close_redis_client(client: Any) -> None:
    """Close a Redis client without replacing the caller's primary outcome."""
    try:
        await client.aclose()
    except Exception:
        logger.warning("Crawler coordination client close failed")


class RedisCrawlerLease:
    """Owner-checked Redis lease with automatic renewal and safe release."""

    RENEW_SCRIPT = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('expire', KEYS[1], ARGV[2])
        end
        return 0
    """
    RELEASE_SCRIPT = """
        if redis.call('get', KEYS[1]) == ARGV[1] then
            return redis.call('del', KEYS[1])
        end
        return 0
    """

    def __init__(
        self,
        client: Any,
        *,
        key: str,
        owner_token: str,
        ttl_seconds: int,
        renew_interval_seconds: float,
    ) -> None:
        if ttl_seconds < 2:
            raise ValueError("Crawler lease TTL must be at least 2 seconds")
        if not 0 < renew_interval_seconds < ttl_seconds:
            raise ValueError("Crawler lease renewal interval must be below its TTL")

        self.client = client
        self.key = key
        self.owner_token = owner_token
        self.ttl_seconds = ttl_seconds
        self.renew_interval_seconds = renew_interval_seconds
        self._stop_event = asyncio.Event()
        self._renewal_task: asyncio.Task[None] | None = None
        self._lost_reason: str | None = None

    @classmethod
    async def acquire(
        cls,
        client_factory: Callable[[], Any],
        *,
        key: str,
        ttl_seconds: int,
        renew_interval_seconds: float,
    ) -> "RedisCrawlerLease":
        """Acquire a new lease or fail closed when Redis cannot decide."""
        try:
            client = client_factory()
        except Exception:
            raise CrawlerCoordinationUnavailableError(
                "Crawler coordination service is unavailable"
            ) from None

        owner_token = uuid.uuid4().hex
        try:
            acquired = await client.set(
                key,
                owner_token,
                nx=True,
                ex=ttl_seconds,
            )
        except asyncio.CancelledError:
            await _safe_close_redis_client(client)
            raise
        except Exception:
            await _safe_close_redis_client(client)
            raise CrawlerCoordinationUnavailableError(
                "Crawler coordination service is unavailable"
            ) from None

        if not acquired:
            await _safe_close_redis_client(client)
            raise CrawlerAlreadyRunningError("Crawler is already running")

        lease = cls(
            client,
            key=key,
            owner_token=owner_token,
            ttl_seconds=ttl_seconds,
            renew_interval_seconds=renew_interval_seconds,
        )
        lease.start_renewal()
        return lease

    def start_renewal(self) -> None:
        """Start one renewal loop for the acquired lease."""
        if self._renewal_task and not self._renewal_task.done():
            return
        self._stop_event.clear()
        self._renewal_task = asyncio.create_task(self._renew_loop())

    async def ensure_owned(self) -> None:
        """Atomically verify ownership and extend the lease before a commit."""
        if self._lost_reason is not None:
            self._raise_lost()

        renewed = await self._compare_and_expire()
        if not renewed:
            self._raise_lost()

    async def release(self) -> None:
        """Stop renewal, delete only this owner's key, and close the client."""
        self._stop_event.set()
        if self._renewal_task is not None:
            try:
                await self._renewal_task
            except asyncio.CancelledError:
                pass
            self._renewal_task = None

        try:
            await self.client.eval(
                self.RELEASE_SCRIPT,
                1,
                self.key,
                self.owner_token,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.warning("Crawler lease release failed")
        finally:
            await _safe_close_redis_client(self.client)

    async def _renew_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                await asyncio.wait_for(
                    self._stop_event.wait(),
                    timeout=self.renew_interval_seconds,
                )
                return
            except asyncio.TimeoutError:
                pass

            if not await self._compare_and_expire():
                return

    async def _compare_and_expire(self) -> bool:
        try:
            renewed = await self.client.eval(
                self.RENEW_SCRIPT,
                1,
                self.key,
                self.owner_token,
                self.ttl_seconds,
            )
        except asyncio.CancelledError:
            raise
        except Exception:
            self._lost_reason = self._lost_reason or "unavailable"
            return False

        if int(renewed or 0) != 1:
            self._lost_reason = self._lost_reason or "lost"
            return False
        return True

    def _raise_lost(self) -> None:
        if self._lost_reason == "unavailable":
            raise CrawlerCoordinationUnavailableError(
                "Crawler coordination service is unavailable"
            )
        raise CrawlerLeaseLostError("Crawler lease ownership was lost")


@dataclass
class CrawlerRunResult:
    """Summary of one crawler execution."""

    imported_count: int
    updated_count: int
    skipped_count: int
    total_count: int
    started_at: datetime
    finished_at: datetime
    message: str


class Source1024SyncService:
    """Upsert logic for resources synchronized from 1024zyz.com."""

    SOURCE_TYPE = "crawler_1024"
    SOURCE_SITE = "1024zyz.com"
    IMPORT_SORT_ORDER = -10
    OPTIONAL_FIELD_KEYS = {
        "excerpt",
        "cover_image_url",
        "resource_type",
        "external_published_at",
        "tags",
    }

    def __init__(
        self, db: AsyncSession, *, enabled_fields: Optional[list[str]] = None
    ) -> None:
        self.db = db
        selected_fields = (
            set(self.OPTIONAL_FIELD_KEYS)
            if enabled_fields is None
            else set(enabled_fields)
        )
        self.enabled_fields = selected_fields & self.OPTIONAL_FIELD_KEYS

    def _is_enabled(self, field_key: str) -> bool:
        return (
            field_key not in self.OPTIONAL_FIELD_KEYS
            or field_key in self.enabled_fields
        )

    async def sync(
        self,
        *,
        max_pages: int,
        timeout_seconds: int,
        target_category_id: Optional[int] = None,
    ) -> CrawlerRunResult:
        started_at = utc_now()
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        crawler = Source1024Crawler(timeout_seconds=timeout_seconds)
        candidates = await crawler.crawl(max_pages=max_pages)
        synced_at = utc_now()

        (
            existing_by_external_id,
            existing_by_source_url,
        ) = await self._load_existing_resources(candidates)
        occupied_slugs = await self._load_occupied_slugs()

        for candidate in candidates:
            existing = self._find_existing_resource(
                candidate,
                existing_by_external_id,
                existing_by_source_url,
            )
            if existing is None:
                resource = self._build_new_resource(
                    candidate,
                    synced_at,
                    target_category_id,
                    occupied_slugs,
                )
                self.db.add(resource)
                self._index_resource(
                    resource,
                    existing_by_external_id,
                    existing_by_source_url,
                )
                imported_count += 1
                continue

            previous_source_site = existing.source_site
            previous_external_id = existing.source_external_id
            previous_source_url = existing.source_url
            if self._update_existing_resource(
                existing, candidate, synced_at, target_category_id
            ):
                updated_count += 1
            else:
                skipped_count += 1
            self._reindex_resource(
                existing,
                existing_by_external_id,
                existing_by_source_url,
                previous_source_site=previous_source_site,
                previous_external_id=previous_external_id,
                previous_source_url=previous_source_url,
            )

        if imported_count:
            # Validate all inserts once. In-memory indexes above make per-row
            # flushes unnecessary while preserving duplicate-candidate handling.
            await self.db.flush()

        finished_at = utc_now()
        total_count = imported_count + updated_count
        message = f"Imported {imported_count}, updated {updated_count}, skipped {skipped_count}"

        return CrawlerRunResult(
            imported_count=imported_count,
            updated_count=updated_count,
            skipped_count=skipped_count,
            total_count=total_count,
            started_at=started_at,
            finished_at=finished_at,
            message=message,
        )

    async def _load_existing_resources(
        self,
        candidates: list[ExternalResourceCandidate],
    ) -> tuple[dict[str, Resource], dict[str, Resource]]:
        external_ids = {candidate.external_id for candidate in candidates}
        source_urls = {candidate.source_url for candidate in candidates}
        if not external_ids and not source_urls:
            return {}, {}

        filters = []
        if external_ids:
            filters.append(
                (Resource.source_site == self.SOURCE_SITE)
                & (Resource.source_external_id.in_(external_ids))
            )
        if source_urls:
            filters.append(Resource.source_url.in_(source_urls))

        result = await self.db.execute(
            select(Resource).where(or_(*filters)).order_by(Resource.id)
        )
        by_external_id: dict[str, Resource] = {}
        by_source_url: dict[str, Resource] = {}
        for resource in result.scalars():
            self._index_resource(resource, by_external_id, by_source_url)
        return by_external_id, by_source_url

    async def _load_occupied_slugs(self) -> set[str]:
        result = await self.db.execute(select(Resource.slug))
        return set(result.scalars())

    def _find_existing_resource(
        self,
        candidate: ExternalResourceCandidate,
        by_external_id: dict[str, Resource],
        by_source_url: dict[str, Resource],
    ) -> Resource | None:
        external_match = by_external_id.get(candidate.external_id)
        url_match = by_source_url.get(candidate.source_url)
        if (
            external_match is not None
            and url_match is not None
            and external_match is not url_match
        ):
            raise RuntimeError(
                "Crawler candidate matches conflicting resources by external ID and URL"
            )
        return external_match or url_match

    def _index_resource(
        self,
        resource: Resource,
        by_external_id: dict[str, Resource],
        by_source_url: dict[str, Resource],
    ) -> None:
        if resource.source_site == self.SOURCE_SITE and resource.source_external_id:
            existing = by_external_id.get(resource.source_external_id)
            if existing is not None and existing is not resource:
                raise RuntimeError("Duplicate crawler external ID found in resources")
            by_external_id[resource.source_external_id] = resource

        if resource.source_url:
            existing = by_source_url.get(resource.source_url)
            if existing is not None and existing is not resource:
                raise RuntimeError("Duplicate crawler source URL found in resources")
            by_source_url[resource.source_url] = resource

    def _reindex_resource(
        self,
        resource: Resource,
        by_external_id: dict[str, Resource],
        by_source_url: dict[str, Resource],
        *,
        previous_source_site: str | None,
        previous_external_id: str | None,
        previous_source_url: str | None,
    ) -> None:
        if (
            previous_source_site == self.SOURCE_SITE
            and previous_external_id
            and previous_external_id != resource.source_external_id
            and by_external_id.get(previous_external_id) is resource
        ):
            del by_external_id[previous_external_id]
        if (
            previous_source_url
            and previous_source_url != resource.source_url
            and by_source_url.get(previous_source_url) is resource
        ):
            del by_source_url[previous_source_url]

        self._index_resource(resource, by_external_id, by_source_url)

    def _build_new_resource(
        self,
        candidate: ExternalResourceCandidate,
        synced_at: datetime,
        target_category_id: Optional[int],
        occupied_slugs: set[str],
    ) -> Resource:
        slug = self._generate_unique_slug(
            candidate.title,
            candidate.external_id,
            occupied_slugs,
        )

        return Resource(
            title=candidate.title,
            slug=slug,
            description=(candidate.excerpt if self._is_enabled("excerpt") else None)
            or candidate.title,
            excerpt=candidate.excerpt if self._is_enabled("excerpt") else None,
            category_id=target_category_id,
            tags=candidate.tags if self._is_enabled("tags") else [],
            price=0,
            is_free=True,
            cover_image_url=candidate.cover_image_url
            if self._is_enabled("cover_image_url")
            else None,
            resource_type=candidate.resource_type
            if self._is_enabled("resource_type")
            else None,
            is_published=False,
            is_featured=False,
            sort_order=self.IMPORT_SORT_ORDER,
            published_at=None,
            source_type=self.SOURCE_TYPE,
            source_site=self.SOURCE_SITE,
            source_url=candidate.source_url,
            source_external_id=candidate.external_id,
            source_last_synced_at=synced_at,
        )

    def _update_existing_resource(
        self,
        resource: Resource,
        candidate: ExternalResourceCandidate,
        synced_at: datetime,
        target_category_id: Optional[int],
    ) -> bool:
        updated = False

        field_updates = {
            "title": candidate.title,
            "source_type": self.SOURCE_TYPE,
            "source_site": self.SOURCE_SITE,
            "source_url": candidate.source_url,
            "source_external_id": candidate.external_id,
        }

        if self._is_enabled("excerpt"):
            field_updates["description"] = (
                candidate.excerpt or resource.description or candidate.title
            )
            field_updates["excerpt"] = candidate.excerpt

        if self._is_enabled("cover_image_url"):
            field_updates["cover_image_url"] = candidate.cover_image_url

        if self._is_enabled("resource_type"):
            field_updates["resource_type"] = candidate.resource_type

        for field_name, new_value in field_updates.items():
            if new_value is None:
                continue
            if getattr(resource, field_name) != new_value:
                setattr(resource, field_name, new_value)
                updated = True

        if target_category_id and resource.category_id is None:
            resource.category_id = target_category_id
            updated = True

        if self._is_enabled("tags") and not resource.tags and candidate.tags:
            resource.tags = candidate.tags
            updated = True

        if (
            resource.sort_order != self.IMPORT_SORT_ORDER
            and resource.source_type == self.SOURCE_TYPE
        ):
            resource.sort_order = self.IMPORT_SORT_ORDER
            updated = True

        resource.source_last_synced_at = synced_at
        return updated

    @staticmethod
    def _generate_unique_slug(
        title: str,
        external_id: str,
        occupied_slugs: set[str],
    ) -> str:
        base_slug = generate_slug(title) or f"external-resource-{external_id}"
        candidate_slug = base_slug
        suffix = 1

        while candidate_slug in occupied_slugs:
            suffix += 1
            candidate_slug = f"{base_slug}-{external_id}-{suffix}"

        occupied_slugs.add(candidate_slug)
        return candidate_slug


class Source1024CrawlerManager:
    """Coordinates manual and scheduled runs for the 1024 crawler."""

    SOURCE_KEY = "crawler_1024"
    SOURCE_NAME = "1024 resources"
    SOURCE_SITE = "1024zyz.com"
    LEASE_KEY = "crawler:1024:lease"
    ACTIVE_RUN_SETTING_KEY = "crawler_1024_active_run_id"
    DEFAULT_LEASE_TTL_SECONDS = 120
    DEFAULT_RENEW_INTERVAL_SECONDS = 30.0

    def __init__(
        self,
        *,
        redis_client_factory: Callable[[], Any] | None = None,
        lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
        renew_interval_seconds: float = DEFAULT_RENEW_INTERVAL_SECONDS,
    ) -> None:
        self._lock = asyncio.Lock()
        self._redis_client_factory = (
            redis_client_factory or _create_crawler_redis_client
        )
        self._lease_ttl_seconds = lease_ttl_seconds
        self._renew_interval_seconds = renew_interval_seconds

    @property
    def is_running(self) -> bool:
        return self._lock.locked()

    async def get_status(self, db: AsyncSession) -> dict:
        settings = await get_1024_crawler_settings(db)
        distributed_lease_active = await self._distributed_lease_is_active()
        if distributed_lease_active is None:
            is_running = self.is_running or settings.last_status == "running"
        else:
            is_running = self.is_running or distributed_lease_active
        enabled_field_set = set(settings.enabled_fields)
        return {
            "source_key": self.SOURCE_KEY,
            "source_name": self.SOURCE_NAME,
            "source_site": self.SOURCE_SITE,
            "enabled": settings.enabled,
            "interval_minutes": settings.interval_minutes,
            "max_pages": settings.max_pages,
            "request_timeout_seconds": settings.request_timeout_seconds,
            "target_category_id": settings.target_category_id,
            "available_fields": [
                {
                    **field,
                    "enabled": field["required"] or field["key"] in enabled_field_set,
                }
                for field in CRAWLER_FIELD_OPTIONS
            ],
            "is_running": is_running,
            "last_run_at": settings.last_run_at,
            "last_status": settings.last_status,
            "last_message": settings.last_message,
            "last_count": settings.last_count,
        }

    async def _distributed_lease_is_active(self) -> bool | None:
        """Return lease presence, or None when Redis cannot answer safely."""
        try:
            client = self._redis_client_factory()
        except Exception:
            return None

        try:
            return bool(await client.exists(self.LEASE_KEY))
        except asyncio.CancelledError:
            raise
        except Exception:
            return None
        finally:
            await _safe_close_redis_client(client)

    async def run(
        self,
        db: AsyncSession,
        *,
        trigger: str,
        updated_by: str = "system",
    ) -> CrawlerRunResult:
        if self.is_running:
            raise CrawlerAlreadyRunningError("Crawler is already running")

        async with self._lock:
            lease = await self._acquire_lease()

            try:
                settings = await get_1024_crawler_settings(db)
                await self._mark_running(
                    db,
                    lease=lease,
                    trigger=trigger,
                    last_count=settings.last_count,
                    updated_by=updated_by,
                )

                service = Source1024SyncService(
                    db,
                    enabled_fields=settings.enabled_fields,
                )
                result = await service.sync(
                    max_pages=settings.max_pages,
                    timeout_seconds=settings.request_timeout_seconds,
                    target_category_id=settings.target_category_id,
                )

                await self._commit_success_if_owned(
                    db,
                    lease=lease,
                    result=result,
                    updated_by=updated_by,
                )
                logger.info(
                    "1024 crawler finished",
                    extra={
                        "trigger": trigger,
                        "imported_count": result.imported_count,
                        "updated_count": result.updated_count,
                        "skipped_count": result.skipped_count,
                    },
                )
                return result
            except asyncio.CancelledError:
                await db.rollback()
                await self._record_terminal_status_if_owned(
                    db,
                    lease=lease,
                    status="cancelled",
                    last_message=f"{trigger} was cancelled",
                    last_count=0,
                    last_run_at=utc_now(),
                    updated_by=updated_by,
                )
                logger.info("1024 crawler cancelled", extra={"trigger": trigger})
                raise
            except Exception as exc:
                await db.rollback()
                error_type = type(exc).__name__
                error_message = f"{trigger} failed ({error_type})"
                await self._record_terminal_status_if_owned(
                    db,
                    lease=lease,
                    status="failed",
                    last_message=error_message,
                    last_count=0,
                    last_run_at=utc_now(),
                    updated_by=updated_by,
                )
                logger.error(
                    "1024 crawler failed",
                    extra={"trigger": trigger, "error_type": error_type},
                )
                raise
            finally:
                await lease.release()

    async def _acquire_lease(self) -> RedisCrawlerLease:
        return await RedisCrawlerLease.acquire(
            self._redis_client_factory,
            key=self.LEASE_KEY,
            ttl_seconds=self._lease_ttl_seconds,
            renew_interval_seconds=self._renew_interval_seconds,
        )

    async def _mark_running(
        self,
        db: AsyncSession,
        *,
        lease: RedisCrawlerLease,
        trigger: str,
        last_count: int,
        updated_by: str,
    ) -> None:
        await upsert_setting(
            db,
            key=self.ACTIVE_RUN_SETTING_KEY,
            value=lease.owner_token,
            description="Owner token for the active crawler execution.",
            updated_by=updated_by,
        )
        await self._update_runtime_status(
            db,
            status="running",
            last_message=f"{trigger} is running",
            last_count=last_count,
            updated_by=updated_by,
        )
        await lease.ensure_owned()
        await db.commit()

    async def _commit_success_if_owned(
        self,
        db: AsyncSession,
        *,
        lease: RedisCrawlerLease,
        result: CrawlerRunResult,
        updated_by: str,
    ) -> None:
        await lease.ensure_owned()
        await self._assert_active_run_owner(db, lease)
        await self._update_runtime_status(
            db,
            status="success",
            last_message=result.message,
            last_count=result.total_count,
            last_run_at=result.finished_at,
            updated_by=updated_by,
        )
        await self._clear_active_run_owner(db, updated_by=updated_by)
        await lease.ensure_owned()
        await db.commit()

    async def _record_terminal_status_if_owned(
        self,
        db: AsyncSession,
        *,
        lease: RedisCrawlerLease,
        status: str,
        last_message: str,
        last_count: int,
        last_run_at: datetime,
        updated_by: str,
    ) -> bool:
        """Persist a terminal state only while both lease owners still match."""
        try:
            await lease.ensure_owned()
            await self._assert_active_run_owner(db, lease)
            await self._update_runtime_status(
                db,
                status=status,
                last_message=last_message,
                last_count=last_count,
                last_run_at=last_run_at,
                updated_by=updated_by,
            )
            await self._clear_active_run_owner(db, updated_by=updated_by)
            await lease.ensure_owned()
            await db.commit()
            return True
        except CrawlerCoordinationUnavailableError:
            await db.rollback()
            return False
        except Exception:
            await db.rollback()
            logger.exception(
                "Crawler terminal status update failed",
                extra={"status": status},
            )
            return False

    async def _assert_active_run_owner(
        self,
        db: AsyncSession,
        lease: RedisCrawlerLease,
    ) -> None:
        active_owner = await db.scalar(
            select(SiteSetting.value).where(
                SiteSetting.key == self.ACTIVE_RUN_SETTING_KEY
            )
        )
        if active_owner != lease.owner_token:
            raise CrawlerLeaseLostError("Crawler status ownership was lost")

    async def _clear_active_run_owner(
        self,
        db: AsyncSession,
        *,
        updated_by: str,
    ) -> None:
        await upsert_setting(
            db,
            key=self.ACTIVE_RUN_SETTING_KEY,
            value="",
            description="Owner token for the active crawler execution.",
            updated_by=updated_by,
        )

    async def _update_runtime_status(
        self,
        db: AsyncSession,
        *,
        status: str,
        last_message: str,
        last_count: int,
        updated_by: str,
        last_run_at: Optional[datetime] = None,
    ) -> None:
        await upsert_setting(
            db,
            key="crawler_1024_last_status",
            value=status,
            description="Last crawler execution status.",
            updated_by=updated_by,
        )
        await upsert_setting(
            db,
            key="crawler_1024_last_message",
            value=last_message,
            description="Last crawler execution summary message.",
            updated_by=updated_by,
        )
        await upsert_setting(
            db,
            key="crawler_1024_last_count",
            value=str(max(last_count, 0)),
            description="Last crawler execution synced resource count.",
            updated_by=updated_by,
        )

        if last_run_at is not None:
            await upsert_setting(
                db,
                key="crawler_1024_last_run_at",
                value=last_run_at.isoformat(),
                description="Last successful or failed crawler execution timestamp in UTC.",
                updated_by=updated_by,
            )


class CrawlerScheduler:
    """Simple in-process scheduler for crawler execution."""

    def __init__(self, manager: Source1024CrawlerManager) -> None:
        self.manager = manager
        self._task: asyncio.Task | None = None
        self._stop_event = asyncio.Event()

    def start(self) -> None:
        if self._task and not self._task.done():
            return

        self._stop_event.clear()
        self._task = asyncio.create_task(self._run_loop())
        logger.info("Crawler scheduler started")

    async def stop(self) -> None:
        if self._task is None:
            return

        self._stop_event.set()
        self._task.cancel()
        try:
            await self._task
        except asyncio.CancelledError:
            pass
        self._task = None
        logger.info("Crawler scheduler stopped")

    async def _run_loop(self) -> None:
        while not self._stop_event.is_set():
            try:
                async with AsyncSessionLocal() as db:
                    status = await self.manager.get_status(db)
                    if self._should_run(status):
                        await self.manager.run(
                            db, trigger="scheduler", updated_by="scheduler"
                        )
            except asyncio.CancelledError:
                raise
            except CrawlerAlreadyRunningError:
                logger.info("Crawler scheduler skipped because another run is active")
            except CrawlerCoordinationUnavailableError:
                logger.warning(
                    "Crawler scheduler skipped because coordination is unavailable"
                )
            except Exception:
                logger.exception("Crawler scheduler loop failed")

            try:
                await asyncio.wait_for(self._stop_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                continue

    @staticmethod
    def _should_run(status: dict) -> bool:
        if status["is_running"] or not status["enabled"]:
            return False

        last_run_at = status.get("last_run_at")
        if last_run_at is None:
            return True

        interval = timedelta(minutes=max(int(status.get("interval_minutes", 180)), 10))
        return utc_now() - last_run_at >= interval


source_1024_crawler_manager = Source1024CrawlerManager()
crawler_scheduler = CrawlerScheduler(source_1024_crawler_manager)
