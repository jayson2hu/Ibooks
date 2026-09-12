"""
Tests for site settings APIs.
"""
import pytest
from httpx import AsyncClient

from app.api.v1 import settings as settings_api
from app.database import AsyncSessionLocal
from app.main import app
from app.models.site_settings import SiteSetting
from app.models.user import User, UserRole
from app.services.site_settings import SIGNIN_REWARD_COINS_KEY
from app.utils.security import create_access_token, get_password_hash


async def create_user(email: str, role: UserRole = UserRole.USER) -> tuple[User, str]:
    """Create a user and return it with an auth token."""
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
            data={"sub": user.id, "email": user.email, "role": user.role.value}
        )
        return user, token


async def create_setting(
    key: str,
    value: str,
    *,
    category: str = "general",
    description: str | None = None,
    updated_by: str | None = None,
) -> SiteSetting:
    """Create a site setting for API tests."""
    async with AsyncSessionLocal() as session:
        setting = SiteSetting(
            key=key,
            value=value,
            category=category,
            description=description,
            updated_by=updated_by,
        )
        session.add(setting)
        await session.commit()
        await session.refresh(setting)
        return setting


@pytest.mark.asyncio
async def test_public_settings_only_return_allowlisted_keys_and_support_filtering():
    """Category membership cannot accidentally make private values public."""
    await create_setting(
        "site_name",
        "Ibooks",
        category="general",
        description="Public site title",
        updated_by="seed-administrator",
    )
    await create_setting("admin_email", "private@example.com", category="general")
    await create_setting("unknown_general", "private", category="general")
    await create_setting("theme_mode", "light", category="appearance")
    await create_setting("copyright_text", "2026", category="footer")
    await create_setting("signin_enabled", "true", category="signin")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/settings")
        filtered_response = await client.get("/api/v1/settings", params={"category": "appearance"})
        private_filtered_response = await client.get("/api/v1/settings", params={"category": "signin"})
        detail_response = await client.get("/api/v1/settings/site_name")
        private_general_response = await client.get("/api/v1/settings/admin_email")
        private_detail_response = await client.get("/api/v1/settings/signin_enabled")

    assert response.status_code == 200
    assert {item["key"] for item in response.json()} == {
        "site_name",
        "theme_mode",
        "copyright_text",
    }

    assert filtered_response.status_code == 200
    assert [item["key"] for item in filtered_response.json()] == ["theme_mode"]

    assert private_filtered_response.status_code == 200
    assert private_filtered_response.json() == []

    assert detail_response.status_code == 200
    assert detail_response.json() == {"key": "site_name", "value": "Ibooks"}
    assert private_general_response.status_code == 404
    assert private_detail_response.status_code == 404

    for item in response.json():
        assert set(item) == {"key", "value"}


@pytest.mark.asyncio
async def test_regular_user_cannot_access_admin_settings_endpoints():
    """Settings admin endpoints reject regular users."""
    _, token = await create_user("settings-user@example.com")
    await create_setting("site_name", "Ibooks")

    async with AsyncClient(app=app, base_url="http://test") as client:
        admin_response = await client.get(
            "/api/v1/settings/admin",
            headers={"Authorization": f"Bearer {token}"},
        )
        grouped_response = await client.get(
            "/api/v1/settings/grouped",
            headers={"Authorization": f"Bearer {token}"},
        )
        update_response = await client.put(
            "/api/v1/settings/site_name",
            json={"value": "Blocked"},
            headers={"Authorization": f"Bearer {token}"},
        )
        batch_response = await client.post(
            "/api/v1/settings/batch",
            json={"settings": [{"key": "site_name", "value": "Blocked"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        test_email_response = await client.post(
            "/api/v1/settings/test-email",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert admin_response.status_code == 403
    assert grouped_response.status_code == 403
    assert update_response.status_code == 403
    assert batch_response.status_code == 403
    assert test_email_response.status_code == 403


@pytest.mark.asyncio
async def test_anonymous_user_cannot_send_test_email():
    """Anonymous callers cannot exercise the SMTP integration."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/settings/test-email")

    assert response.status_code in {401, 403}


@pytest.mark.asyncio
async def test_admin_test_email_uses_current_admin_and_fixed_content(monkeypatch):
    """The endpoint never accepts an arbitrary recipient or message body."""
    admin, token = await create_user("smtp-admin@example.com", UserRole.ADMIN)
    messages: list[dict[str, str]] = []

    async def capture_email(to: str, subject: str, html_body: str) -> bool:
        messages.append({"to": to, "subject": subject, "html_body": html_body})
        return True

    monkeypatch.setattr(settings_api.email_utils, "send_email", capture_email)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/settings/test-email",
            json={
                "to": "attacker@example.com",
                "subject": "Untrusted subject",
                "html_body": "<script>alert('xss')</script>",
            },
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json() == {"message": "测试邮件已发送到当前管理员邮箱"}
    assert messages == [
        {
            "to": admin.email,
            "subject": settings_api.TEST_EMAIL_SUBJECT,
            "html_body": settings_api.TEST_EMAIL_BODY,
        }
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize("failure_mode", ["not_configured", "unexpected_error"])
async def test_admin_test_email_returns_safe_503_on_delivery_failure(
    monkeypatch,
    caplog,
    failure_mode: str,
):
    """Configuration and provider failures share a credential-safe response."""
    _, token = await create_user(
        f"smtp-failure-{failure_mode}@example.com",
        UserRole.ADMIN,
    )

    if failure_mode == "not_configured":
        monkeypatch.setattr(settings_api.email_utils.settings, "EMAIL_FROM", "")
        monkeypatch.setattr(settings_api.email_utils.settings, "EMAIL_USERNAME", "")
        monkeypatch.setattr(settings_api.email_utils.settings, "EMAIL_PASSWORD", "")

        def unexpected_smtp_call(to: str, subject: str, html_body: str) -> None:
            raise AssertionError("SMTP must not be called without credentials")

        monkeypatch.setattr(
            settings_api.email_utils,
            "_send_email_sync",
            unexpected_smtp_call,
        )
    else:
        async def fail_email(to: str, subject: str, html_body: str) -> bool:
            raise RuntimeError(
                "smtp-password=secret recipient=private@example.com internal-host=smtp.local"
            )

        monkeypatch.setattr(settings_api.email_utils, "send_email", fail_email)

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/settings/test-email",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 503
    assert response.json() == {"detail": settings_api.TEST_EMAIL_FAILURE_MESSAGE}
    observable_text = response.text + " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in caplog.records
    )
    assert "smtp-password" not in observable_text
    assert "private@example.com" not in observable_text
    assert "smtp.local" not in observable_text


@pytest.mark.asyncio
async def test_admin_can_list_all_settings_and_group_by_category():
    """Admins can read private settings and grouped settings."""
    _, token = await create_user("settings-admin@example.com", UserRole.ADMIN)
    await create_setting("site_name", "Ibooks", category="general")
    await create_setting("signin_enabled", "true", category="signin")

    async with AsyncClient(app=app, base_url="http://test") as client:
        admin_response = await client.get(
            "/api/v1/settings/admin",
            headers={"Authorization": f"Bearer {token}"},
        )
        grouped_response = await client.get(
            "/api/v1/settings/grouped",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert admin_response.status_code == 200
    assert {item["key"] for item in admin_response.json()} == {"site_name", "signin_enabled"}

    assert grouped_response.status_code == 200
    grouped = {item["category"]: {setting["key"] for setting in item["settings"]} for item in grouped_response.json()}
    assert grouped == {
        "general": {"site_name"},
        "signin": {"signin_enabled"},
    }


@pytest.mark.asyncio
async def test_admin_can_update_existing_setting_and_missing_setting_returns_404():
    """Admins can update an existing setting by key."""
    admin, token = await create_user("settings-update-admin@example.com", UserRole.ADMIN)
    await create_setting("site_name", "Ibooks")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.put(
            "/api/v1/settings/site_name",
            json={"value": "Ibooks Pro", "updated_by": "spoofed-operator"},
            headers={"Authorization": f"Bearer {token}"},
        )
        missing_response = await client.put(
            "/api/v1/settings/missing_key",
            json={"value": "Missing"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["value"] == "Ibooks Pro"
    assert response.json()["updated_by"] == admin.username
    assert response.json()["updated_by"] != "spoofed-operator"
    assert missing_response.status_code == 404


@pytest.mark.asyncio
async def test_admin_batch_update_updates_existing_and_creates_new_settings():
    """Batch update modifies existing settings and creates missing settings."""
    admin, token = await create_user("settings-batch-admin@example.com", UserRole.ADMIN)
    await create_setting("site_name", "Ibooks")

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/settings/batch",
            json={
                "settings": [
                    {"key": "site_name", "value": "Ibooks Pro"},
                    {"key": "new_footer", "value": "Footer", "category": "footer"},
                    {"key": "", "value": "Ignored"},
                    {"key": "missing_value"},
                ]
            },
            headers={"Authorization": f"Bearer {token}"},
        )
        settings_response = await client.get(
            "/api/v1/settings/admin",
            headers={"Authorization": f"Bearer {token}"},
        )

    assert response.status_code == 200
    assert response.json()["message"] == "Successfully updated 2 settings"
    settings = {item["key"]: item for item in settings_response.json()}
    assert settings["site_name"]["value"] == "Ibooks Pro"
    assert settings["site_name"]["updated_by"] == admin.username
    assert settings["new_footer"]["category"] == "footer"
    assert settings["new_footer"]["updated_by"] == admin.username


@pytest.mark.asyncio
async def test_signin_reward_setting_requires_positive_integer():
    """Signin reward setting rejects non-positive and non-integer values."""
    _, token = await create_user("settings-signin-admin@example.com", UserRole.ADMIN)
    await create_setting(SIGNIN_REWARD_COINS_KEY, "5", category="signin")

    async with AsyncClient(app=app, base_url="http://test") as client:
        text_response = await client.put(
            f"/api/v1/settings/{SIGNIN_REWARD_COINS_KEY}",
            json={"value": "many"},
            headers={"Authorization": f"Bearer {token}"},
        )
        zero_response = await client.post(
            "/api/v1/settings/batch",
            json={"settings": [{"key": SIGNIN_REWARD_COINS_KEY, "value": "0"}]},
            headers={"Authorization": f"Bearer {token}"},
        )
        valid_response = await client.put(
            f"/api/v1/settings/{SIGNIN_REWARD_COINS_KEY}",
            json={"value": "8"},
            headers={"Authorization": f"Bearer {token}"},
        )

    assert text_response.status_code == 400
    assert zero_response.status_code == 400
    assert valid_response.status_code == 200
    assert valid_response.json()["value"] == "8"
