"""Authorization and allowlist tests for crawler configuration APIs."""

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.database import AsyncSessionLocal
from app.main import app
from app.models.category import Category
from app.models.site_settings import SiteSetting
from app.models.user import User, UserRole
from app.services.crawler_service import (
    CrawlerAlreadyRunningError,
    CrawlerCoordinationUnavailableError,
)
from app.utils.security import create_access_token, get_password_hash


VALID_CONFIG = {
    "enabled": True,
    "interval_minutes": 60,
    "max_pages": 3,
    "request_timeout_seconds": 20,
    "target_category_id": None,
    "enabled_fields": ["tags", "excerpt"],
}

CONFIG_SETTING_KEYS = {
    "crawler_1024_enabled",
    "crawler_1024_interval_minutes",
    "crawler_1024_max_pages",
    "crawler_1024_request_timeout_seconds",
    "crawler_1024_target_category_id",
    "crawler_1024_enabled_fields",
}


async def create_user(email: str, role: UserRole) -> tuple[User, str]:
    """Create an active user and a signed access token."""
    async with AsyncSessionLocal() as session:
        user = User(
            email=email,
            username=email.split("@")[0],
            role=role,
            password_hash=get_password_hash("Test1234"),
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        token = create_access_token(
            {"sub": user.id, "email": user.email, "role": user.role.value}
        )
        return user, token


async def create_category() -> Category:
    """Create a valid target category for crawler configuration."""
    async with AsyncSessionLocal() as session:
        category = Category(name="Crawler Target", slug="crawler-target")
        session.add(category)
        await session.commit()
        await session.refresh(category)
        return category


@pytest.mark.asyncio
@pytest.mark.parametrize("role", [UserRole.ADMIN, UserRole.MODERATOR])
async def test_staff_can_read_and_update_only_crawler_config(role: UserRole):
    """Both staff roles can use the dedicated typed crawler configuration API."""
    staff, token = await create_user(f"crawler-{role.value}@example.com", role)
    category = await create_category()
    payload = {**VALID_CONFIG, "target_category_id": category.id}

    async with AsyncClient(app=app, base_url="http://test") as client:
        initial_response = await client.get(
            "/api/v1/crawler/1024/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        update_response = await client.put(
            "/api/v1/crawler/1024/config",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )
        saved_response = await client.get(
            "/api/v1/crawler/1024/config",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert initial_response.status_code == 200
    assert update_response.status_code == 200
    expected = {
        **payload,
        "enabled_fields": ["excerpt", "tags"],
    }
    assert update_response.json() == expected
    assert saved_response.json() == expected

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SiteSetting).where(SiteSetting.key.in_(CONFIG_SETTING_KEYS))
        )
        saved_settings = result.scalars().all()

    assert {setting.key for setting in saved_settings} == CONFIG_SETTING_KEYS
    assert all(setting.category == "crawler" for setting in saved_settings)
    assert all(setting.updated_by == staff.username for setting in saved_settings)


@pytest.mark.asyncio
async def test_regular_users_cannot_read_or_update_crawler_config():
    """Crawler configuration remains inaccessible to non-staff users."""
    _, token = await create_user("crawler-reader@example.com", UserRole.USER)

    async with AsyncClient(app=app, base_url="http://test") as client:
        read_response = await client.get(
            "/api/v1/crawler/1024/config",
            headers={"Authorization": f"Bearer {token}"},
        )
        update_response = await client.put(
            "/api/v1/crawler/1024/config",
            json=VALID_CONFIG,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert read_response.status_code == 403
    assert update_response.status_code == 403


@pytest.mark.asyncio
async def test_moderator_cannot_use_generic_settings_batch():
    """The dedicated crawler permission must not widen generic setting writes."""
    _, token = await create_user("crawler-moderator@example.com", UserRole.MODERATOR)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/settings/batch",
            json={"settings": [{"key": "site_name", "value": "Compromised"}]},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 403


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "invalid_values",
    [
        {"site_name": "Compromised"},
        {"enabled": "true"},
        {"interval_minutes": "60"},
        {"enabled_fields": ["excerpt", "cloud_link"]},
        {"enabled_fields": ["excerpt", "excerpt"]},
        {"interval_minutes": 9},
        {"max_pages": 51},
        {"request_timeout_seconds": 121},
        {"target_category_id": 0},
    ],
)
async def test_crawler_config_rejects_unlisted_or_invalid_values(invalid_values):
    """Unknown keys, fields, and unsafe limits fail before any setting is written."""
    _, token = await create_user("crawler-validation@example.com", UserRole.ADMIN)
    payload = {**VALID_CONFIG, **invalid_values}

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            "/api/v1/crawler/1024/config",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 422
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SiteSetting.key).where(SiteSetting.key.in_(CONFIG_SETTING_KEYS))
        )
        assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_crawler_config_rejects_missing_target_category_atomically():
    """A nonexistent target category cannot leave partial crawler settings behind."""
    _, token = await create_user("crawler-target-admin@example.com", UserRole.ADMIN)
    payload = {**VALID_CONFIG, "target_category_id": 999999}

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            "/api/v1/crawler/1024/config",
            json=payload,
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "Target category does not exist"
    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(SiteSetting.key).where(SiteSetting.key.in_(CONFIG_SETTING_KEYS))
        )
        assert result.scalars().all() == []


@pytest.mark.asyncio
async def test_crawler_config_read_normalizes_legacy_unsafe_values():
    """Historical generic setting writes cannot break the strict config response."""
    _, token = await create_user("crawler-legacy-admin@example.com", UserRole.ADMIN)
    legacy_values = {
        "crawler_1024_interval_minutes": "999999",
        "crawler_1024_max_pages": "999",
        "crawler_1024_request_timeout_seconds": "999",
        "crawler_1024_target_category_id": "999999",
        "crawler_1024_enabled_fields": "tags,unknown,tags,excerpt",
    }
    async with AsyncSessionLocal() as session:
        session.add_all(
            SiteSetting(key=key, value=value, category="crawler")
            for key, value in legacy_values.items()
        )
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/crawler/1024/config",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {
        "enabled": False,
        "interval_minutes": 10080,
        "max_pages": 50,
        "request_timeout_seconds": 120,
        "target_category_id": None,
        "enabled_fields": ["excerpt", "tags"],
    }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("crawler_error", "expected_status", "expected_detail"),
    [
        (
            CrawlerAlreadyRunningError("internal detail must not be returned"),
            409,
            "Crawler is already running",
        ),
        (
            CrawlerCoordinationUnavailableError(
                "redis://secret-user:secret-password@internal-host"
            ),
            503,
            "Crawler coordination service is unavailable",
        ),
    ],
)
async def test_crawler_run_maps_coordination_errors_without_leaking_details(
    crawler_error,
    expected_status,
    expected_detail,
    monkeypatch,
):
    _, token = await create_user("crawler-run-admin@example.com", UserRole.ADMIN)

    async def fail_run(*args, **kwargs):
        raise crawler_error

    monkeypatch.setattr(
        "app.api.v1.crawler.source_1024_crawler_manager.run",
        fail_run,
    )

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/crawler/1024/run",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == expected_status
    assert response.json() == {"detail": expected_detail}
