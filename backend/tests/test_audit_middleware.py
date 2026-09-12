"""Tests for durable, failure-isolated request audit logging."""

import pytest
from fastapi import FastAPI, HTTPException, status
from httpx import AsyncClient
from sqlalchemy import select

import app.middleware.audit as audit_module
from app.database import AsyncSessionLocal
from app.middleware.audit import AuditMiddleware
from app.models.audit_log import AuditAction, AuditLog
from app.models.user import User
from app.utils.security import create_access_token, get_password_hash


async def create_user_and_token() -> tuple[User, str]:
    """Create the foreign-key user represented by the test JWT."""
    async with AsyncSessionLocal() as session:
        user = User(
            email="audited@example.com",
            username="audited-user",
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = create_access_token({"sub": user.id, "email": user.email})
        return user, token


def create_test_app() -> FastAPI:
    """Create an isolated app whose routes exercise audit classifications."""
    test_app = FastAPI()

    @test_app.post("/api/v1/resources", status_code=status.HTTP_201_CREATED)
    async def create_resource() -> dict[str, bool]:
        return {"created": True}

    @test_app.get("/api/v1/resources")
    async def list_resources() -> list[object]:
        return []

    @test_app.post("/api/v1/categories")
    async def reject_category() -> None:
        raise HTTPException(status_code=422, detail="Invalid category")

    @test_app.patch("/api/v1/resources/{resource_id}")
    async def update_resource(resource_id: str) -> dict[str, str]:
        return {"resource_id": resource_id}

    @test_app.post("/api/v1/crawler/1024/run")
    async def run_crawler() -> dict[str, bool]:
        return {"started": True}

    test_app.add_middleware(AuditMiddleware)
    return test_app


@pytest.mark.asyncio
async def test_successful_write_is_persisted_without_sensitive_request_data():
    user, token = await create_user_and_token()

    async with AsyncClient(app=create_test_app(), base_url="http://test") as client:
        response = await client.post(
            "/api/v1/resources",
            json={"password": "must-not-be-logged", "title": "Audited resource"},
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "audit-test-agent",
                "X-Forwarded-For": "203.0.113.10, 10.0.0.1",
            },
        )

    assert response.status_code == 201
    async with AsyncSessionLocal() as session:
        audit_log = (await session.execute(select(AuditLog))).scalar_one()

    assert audit_log.action == AuditAction.RESOURCE_CREATE
    assert audit_log.user_id == user.id
    assert audit_log.user_email == user.email
    assert audit_log.ip_address == "127.0.0.1"
    assert audit_log.user_agent == "audit-test-agent"
    assert audit_log.request_method == "POST"
    assert audit_log.request_path == "/api/v1/resources"
    assert audit_log.success is True
    assert audit_log.error_message is None
    assert audit_log.details["status_code"] == 201
    assert audit_log.details["duration_ms"] >= 0
    assert "must-not-be-logged" not in str(audit_log.details)
    assert token not in str(audit_log.details)


@pytest.mark.asyncio
async def test_failed_action_and_not_ordinary_get_are_persisted_correctly():
    async with AsyncClient(app=create_test_app(), base_url="http://test") as client:
        get_response = await client.get("/api/v1/resources")
        failed_response = await client.post("/api/v1/categories")

    assert get_response.status_code == 200
    assert failed_response.status_code == 422
    async with AsyncSessionLocal() as session:
        audit_logs = (await session.execute(select(AuditLog))).scalars().all()

    assert len(audit_logs) == 1
    assert audit_logs[0].action == AuditAction.CATEGORY_CREATE
    assert audit_logs[0].success is False
    assert audit_logs[0].error_message == "HTTP 422"
    assert audit_logs[0].details["status_code"] == 422


@pytest.mark.asyncio
async def test_audit_database_failure_does_not_change_business_response(monkeypatch):
    def broken_session_factory():
        raise RuntimeError("audit database unavailable")

    monkeypatch.setattr(audit_module, "AsyncSessionLocal", broken_session_factory)

    async with AsyncClient(app=create_test_app(), base_url="http://test") as client:
        response = await client.post("/api/v1/resources")

    assert response.status_code == 201
    assert response.json() == {"created": True}


@pytest.mark.asyncio
async def test_stale_token_identity_and_untrusted_metadata_are_safely_bounded():
    token = create_access_token({"sub": 999_999, "email": "e" * 300})
    resource_id = "r" * 600

    async with AsyncClient(app=create_test_app(), base_url="http://test") as client:
        response = await client.patch(
            f"/api/v1/resources/{resource_id}",
            headers={
                "Authorization": f"Bearer {token}",
                "User-Agent": "u" * 1200,
                "X-Forwarded-For": "1" * 100,
            },
        )

    assert response.status_code == 200
    async with AsyncSessionLocal() as session:
        audit_log = (await session.execute(select(AuditLog))).scalar_one()

    assert audit_log.action == AuditAction.RESOURCE_UPDATE
    assert audit_log.user_id is None
    assert audit_log.user_email == "e" * 255
    assert audit_log.ip_address == "127.0.0.1"
    assert audit_log.user_agent == "u" * 1000
    assert len(audit_log.request_path) == 500


@pytest.mark.parametrize(
    ("path", "method", "expected"),
    [
        ("/api/v1/orders", "POST", AuditAction.OTHER),
        ("/api/v1/admin/wallets/12/adjust", "POST", AuditAction.OTHER),
        ("/api/v1/recharge/alipay/notify", "POST", AuditAction.OTHER),
        ("/api/v1/crawler/1024/run", "POST", AuditAction.OTHER),
        ("/api/v1/faqs/3", "PATCH", AuditAction.OTHER),
        ("/api/v1/resources/book/access", "GET", None),
        ("/api/v1/resources/book/download", "POST", AuditAction.RESOURCE_DOWNLOAD),
        ("/api/v1/orders", "GET", None),
        ("/api/v1/crawler/1024/status", "GET", None),
    ],
)
def test_action_mapping_covers_key_writes_without_ordinary_read_noise(
    path: str,
    method: str,
    expected: AuditAction | None,
):
    assert AuditMiddleware._determine_action(path, method) == expected


@pytest.mark.asyncio
async def test_unexpected_audit_error_does_not_change_business_response(monkeypatch):
    async def broken_record_event(*args, **kwargs):
        raise RuntimeError("unexpected audit failure")

    monkeypatch.setattr(AuditMiddleware, "_record_event", broken_record_event)

    async with AsyncClient(app=create_test_app(), base_url="http://test") as client:
        success_response = await client.post("/api/v1/resources")
        error_response = await client.post("/api/v1/categories")

    assert success_response.status_code == 201
    assert success_response.json() == {"created": True}
    assert error_response.status_code == 422
    assert error_response.json() == {"detail": "Invalid category"}
