"""Deterministic tests for crawler distributed coordination."""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime

import pytest
from sqlalchemy import select

from app.models.resource import Resource
from app.models.site_settings import SiteSetting
from app.services.crawler_service import (
    CrawlerAlreadyRunningError,
    CrawlerCoordinationUnavailableError,
    CrawlerLeaseLostError,
    CrawlerRunResult,
    CrawlerScheduler,
    Source1024CrawlerManager,
    Source1024SyncService,
)


class FakeRedisState:
    """Shared Redis state used by independent fake clients/managers."""

    def __init__(self) -> None:
        self.values: dict[str, str] = {}
        self.ttls: dict[str, int] = {}
        self.fail_set = False
        self.fail_eval = False
        self.fail_exists = False
        self.clients: list[FakeRedisClient] = []


class FakeRedisClient:
    """Small fake implementing only the lease commands used by the manager."""

    def __init__(self, state: FakeRedisState) -> None:
        self.state = state
        self.closed = False
        state.clients.append(self)

    async def set(
        self,
        key: str,
        value: str,
        *,
        nx: bool,
        ex: int,
    ) -> bool:
        if self.state.fail_set:
            raise RuntimeError("fake Redis set failure")
        if nx and key in self.state.values:
            return False
        self.state.values[key] = value
        self.state.ttls[key] = ex
        return True

    async def eval(self, script: str, numkeys: int, *args):
        assert numkeys == 1
        if self.state.fail_eval:
            raise RuntimeError("fake Redis eval failure")

        key = args[0]
        owner_token = args[1]
        if self.state.values.get(key) != owner_token:
            return 0

        if "expire" in script:
            self.state.ttls[key] = int(args[2])
            return 1
        if "del" in script:
            del self.state.values[key]
            self.state.ttls.pop(key, None)
            return 1
        raise AssertionError("Unexpected Lua script")

    async def exists(self, key: str) -> int:
        if self.state.fail_exists:
            raise RuntimeError(
                "redis://secret-user:secret-password@internal-host must not leak"
            )
        return int(key in self.state.values)

    async def aclose(self) -> None:
        self.closed = True


def make_manager(state: FakeRedisState) -> Source1024CrawlerManager:
    return Source1024CrawlerManager(
        redis_client_factory=lambda: FakeRedisClient(state),
        lease_ttl_seconds=60,
        renew_interval_seconds=30,
    )


async def save_running_scheduler_settings(db_session) -> None:
    db_session.add_all(
        [
            SiteSetting(
                key="crawler_1024_enabled",
                value="true",
                category="crawler",
            ),
            SiteSetting(
                key="crawler_1024_last_status",
                value="running",
                category="crawler",
            ),
        ]
    )
    await db_session.commit()


@pytest.mark.asyncio
async def test_stale_running_status_without_redis_lease_can_retry(db_session):
    state = FakeRedisState()
    manager = make_manager(state)
    await save_running_scheduler_settings(db_session)

    status = await manager.get_status(db_session)

    assert status["last_status"] == "running"
    assert status["is_running"] is False
    assert CrawlerScheduler._should_run(status) is True
    assert state.clients[-1].closed is True


@pytest.mark.asyncio
async def test_status_detects_lease_owned_by_another_manager(db_session):
    state = FakeRedisState()
    owner_manager = make_manager(state)
    observing_manager = make_manager(state)
    lease = await owner_manager._acquire_lease()

    try:
        status = await observing_manager.get_status(db_session)
        assert status["is_running"] is True
        assert state.clients[-1].closed is True
    finally:
        await lease.release()


@pytest.mark.asyncio
async def test_status_redis_failure_falls_back_without_leaking_details(
    db_session,
    caplog,
):
    state = FakeRedisState()
    state.fail_exists = True
    manager = make_manager(state)
    await save_running_scheduler_settings(db_session)

    status = await manager.get_status(db_session)

    assert status["is_running"] is True
    assert state.clients[-1].closed is True
    assert "secret-password" not in caplog.text
    assert "internal-host" not in caplog.text


@pytest.mark.asyncio
async def test_two_managers_cannot_hold_the_same_distributed_lease():
    state = FakeRedisState()
    first_manager = make_manager(state)
    second_manager = make_manager(state)

    first_lease = await first_manager._acquire_lease()
    try:
        with pytest.raises(CrawlerAlreadyRunningError):
            await second_manager._acquire_lease()
    finally:
        await first_lease.release()

    second_lease = await second_manager._acquire_lease()
    await second_lease.release()
    assert first_manager.LEASE_KEY not in state.values


@pytest.mark.asyncio
async def test_renew_and_release_require_the_same_owner_token():
    state = FakeRedisState()
    manager = make_manager(state)
    lease = await manager._acquire_lease()

    await lease.ensure_owned()
    assert state.ttls[manager.LEASE_KEY] == 60

    state.values[manager.LEASE_KEY] = "replacement-owner"
    with pytest.raises(CrawlerLeaseLostError):
        await lease.ensure_owned()

    await lease.release()
    assert state.values[manager.LEASE_KEY] == "replacement-owner"


@pytest.mark.asyncio
async def test_redis_failure_fails_closed_and_closes_the_client():
    state = FakeRedisState()
    state.fail_set = True
    manager = make_manager(state)

    with pytest.raises(
        CrawlerCoordinationUnavailableError,
        match="coordination service is unavailable",
    ):
        await manager._acquire_lease()

    assert state.clients[-1].closed is True


@pytest.mark.asyncio
async def test_cancellation_rolls_back_and_records_cancelled_status(
    db_session,
    monkeypatch,
):
    state = FakeRedisState()
    manager = make_manager(state)
    entered_sync = asyncio.Event()

    async def blocking_sync(self, **kwargs):
        entered_sync.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(Source1024SyncService, "sync", blocking_sync)

    task = asyncio.create_task(
        manager.run(db_session, trigger="manual", updated_by="tester")
    )
    await asyncio.wait_for(entered_sync.wait(), timeout=2)
    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task

    result = await db_session.execute(
        select(SiteSetting).where(
            SiteSetting.key.in_(
                {
                    manager.ACTIVE_RUN_SETTING_KEY,
                    "crawler_1024_last_status",
                    "crawler_1024_last_message",
                }
            )
        )
    )
    saved = {setting.key: setting.value for setting in result.scalars()}
    assert saved[manager.ACTIVE_RUN_SETTING_KEY] == ""
    assert saved["crawler_1024_last_status"] == "cancelled"
    assert saved["crawler_1024_last_message"] == "manual was cancelled"
    assert manager.LEASE_KEY not in state.values


@pytest.mark.asyncio
async def test_lost_lease_prevents_business_commit_and_status_overwrite(
    db_session,
    monkeypatch,
):
    state = FakeRedisState()
    manager = make_manager(state)

    async def lose_lease_before_return(self, **kwargs):
        self.db.add(
            Resource(
                title="Must roll back",
                slug="must-roll-back",
                description="Must roll back",
                tags=[],
                price=0,
                coin_price=0,
                is_free=True,
                backup_links=[],
                preview_images=[],
                is_published=False,
                is_featured=False,
                sort_order=0,
            )
        )
        state.values[manager.LEASE_KEY] = "replacement-owner"
        now = datetime(2026, 9, 10, 12, 0, 0)
        return CrawlerRunResult(
            imported_count=1,
            updated_count=0,
            skipped_count=0,
            total_count=1,
            started_at=now,
            finished_at=now,
            message="Imported 1, updated 0, skipped 0",
        )

    monkeypatch.setattr(Source1024SyncService, "sync", lose_lease_before_return)

    with pytest.raises(CrawlerLeaseLostError):
        await manager.run(db_session, trigger="manual", updated_by="tester")

    assert (await db_session.execute(select(Resource))).scalars().all() == []
    last_status = await db_session.scalar(
        select(SiteSetting.value).where(
            SiteSetting.key == "crawler_1024_last_status"
        )
    )
    assert last_status == "running"
    assert state.values[manager.LEASE_KEY] == "replacement-owner"


@pytest.mark.asyncio
async def test_failed_run_sanitizes_status_and_logs(db_session, monkeypatch, caplog):
    """Provider and database exception text must not reach staff-visible status."""
    state = FakeRedisState()
    manager = make_manager(state)
    secret = "redis://secret-user:secret-password@internal-host"

    async def fail_sync(self, **kwargs):
        raise RuntimeError(secret)

    monkeypatch.setattr(Source1024SyncService, "sync", fail_sync)

    with caplog.at_level(logging.ERROR, logger="app.services.crawler_service"):
        with pytest.raises(RuntimeError, match="secret-password"):
            await manager.run(db_session, trigger="manual", updated_by="tester")

    last_message = await db_session.scalar(
        select(SiteSetting.value).where(
            SiteSetting.key == "crawler_1024_last_message"
        )
    )
    assert last_message == "manual failed (RuntimeError)"
    assert secret not in caplog.text
