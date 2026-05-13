"""
Synchronization and scheduling for external crawlers.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import AsyncSessionLocal
from app.models.resource import Resource
from app.services.crawlers.source_1024 import (
    CRAWLER_FIELD_OPTIONS,
    ExternalResourceCandidate,
    Source1024Crawler,
)
from app.services.site_settings import get_1024_crawler_settings, upsert_setting
from app.utils.logging import get_logger
from app.utils.seo import generate_slug


logger = get_logger(__name__)


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
        started_at = datetime.utcnow()
        imported_count = 0
        updated_count = 0
        skipped_count = 0

        crawler = Source1024Crawler(timeout_seconds=timeout_seconds)
        candidates = await crawler.crawl(max_pages=max_pages)
        synced_at = datetime.utcnow()

        for candidate in candidates:
            existing = await self._find_existing_resource(candidate)
            if existing is None:
                resource = await self._build_new_resource(
                    candidate, synced_at, target_category_id
                )
                self.db.add(resource)
                # Flush so subsequent _generate_unique_slug lookups can see this row
                # and avoid UNIQUE constraint violations on the slug column.
                await self.db.flush()
                imported_count += 1
                continue

            if self._update_existing_resource(
                existing, candidate, synced_at, target_category_id
            ):
                updated_count += 1
            else:
                skipped_count += 1

        finished_at = datetime.utcnow()
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

    async def _find_existing_resource(
        self, candidate: ExternalResourceCandidate
    ) -> Resource | None:
        result = await self.db.execute(
            select(Resource).where(
                or_(
                    (Resource.source_site == self.SOURCE_SITE)
                    & (Resource.source_external_id == candidate.external_id),
                    Resource.source_url == candidate.source_url,
                )
            )
        )
        return result.scalar_one_or_none()

    async def _build_new_resource(
        self,
        candidate: ExternalResourceCandidate,
        synced_at: datetime,
        target_category_id: Optional[int],
    ) -> Resource:
        slug = await self._generate_unique_slug(candidate.title, candidate.external_id)

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
            is_published=True,
            is_featured=False,
            sort_order=self.IMPORT_SORT_ORDER,
            published_at=(
                candidate.external_published_at
                if self._is_enabled("external_published_at")
                else None
            )
            or synced_at,
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

        if self._is_enabled("tags") and not resource.tags:
            resource.tags = candidate.tags
            updated = True

        if (
            resource.sort_order != self.IMPORT_SORT_ORDER
            and resource.source_type == self.SOURCE_TYPE
        ):
            resource.sort_order = self.IMPORT_SORT_ORDER
            updated = True

        if (
            self._is_enabled("external_published_at")
            and not resource.published_at
            and candidate.external_published_at
        ):
            resource.published_at = candidate.external_published_at
            updated = True

        if not resource.is_published:
            resource.is_published = True
            updated = True

        resource.source_last_synced_at = synced_at
        return updated

    async def _generate_unique_slug(self, title: str, external_id: str) -> str:
        base_slug = generate_slug(title) or f"external-resource-{external_id}"
        candidate_slug = base_slug
        suffix = 1

        while True:
            result = await self.db.execute(
                select(Resource.id).where(Resource.slug == candidate_slug)
            )
            if result.scalar_one_or_none() is None:
                return candidate_slug
            suffix += 1
            candidate_slug = f"{base_slug}-{external_id}-{suffix}"


class Source1024CrawlerManager:
    """Coordinates manual and scheduled runs for the 1024 crawler."""

    SOURCE_KEY = "crawler_1024"
    SOURCE_NAME = "1024 resources"
    SOURCE_SITE = "1024zyz.com"

    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    @property
    def is_running(self) -> bool:
        return self._lock.locked()

    async def get_status(self, db: AsyncSession) -> dict:
        settings = await get_1024_crawler_settings(db)
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
            "is_running": self.is_running,
            "last_run_at": settings.last_run_at,
            "last_status": settings.last_status,
            "last_message": settings.last_message,
            "last_count": settings.last_count,
        }

    async def run(
        self,
        db: AsyncSession,
        *,
        trigger: str,
        updated_by: str = "system",
    ) -> CrawlerRunResult:
        if self.is_running:
            raise RuntimeError("Crawler is already running")

        async with self._lock:
            settings = await get_1024_crawler_settings(db)
            await self._update_runtime_status(
                db,
                status="running",
                last_message=f"{trigger} is running",
                last_count=settings.last_count,
                updated_by=updated_by,
            )
            await db.commit()

            service = Source1024SyncService(db, enabled_fields=settings.enabled_fields)

            try:
                result = await service.sync(
                    max_pages=settings.max_pages,
                    timeout_seconds=settings.request_timeout_seconds,
                    target_category_id=settings.target_category_id,
                )
                await self._update_runtime_status(
                    db,
                    status="success",
                    last_message=result.message,
                    last_count=result.total_count,
                    last_run_at=result.finished_at,
                    updated_by=updated_by,
                )
                await db.commit()
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
            except Exception as exc:
                await db.rollback()
                error_message = f"{trigger} failed: {exc}"
                await self._update_runtime_status(
                    db,
                    status="failed",
                    last_message=error_message,
                    last_count=0,
                    last_run_at=datetime.utcnow(),
                    updated_by=updated_by,
                )
                await db.commit()
                logger.exception("1024 crawler failed", extra={"trigger": trigger})
                raise

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
        return datetime.utcnow() - last_run_at >= interval


source_1024_crawler_manager = Source1024CrawlerManager()
crawler_scheduler = CrawlerScheduler(source_1024_crawler_manager)
