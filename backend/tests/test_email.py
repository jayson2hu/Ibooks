"""
Tests for email verification and password reset flows.
"""
import logging
import smtplib
from datetime import timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.v1 import auth
from app.database import AsyncSessionLocal
from app.main import app
from app.models.user import User
from app.models.wallet import Wallet
from app.utils import email as email_utils
from app.utils.security import verify_password
from app.utils.datetime_utils import utc_now


@pytest.fixture
def email_outbox(monkeypatch):
    """Capture outgoing email without sending SMTP messages."""
    messages = []

    async def fake_send_email(to: str, subject: str, html_body: str) -> bool:
        messages.append({"to": to, "subject": subject, "html_body": html_body})
        return True

    monkeypatch.setattr(auth.email_utils, "send_email", fake_send_email)
    return messages


@pytest.fixture
def reset_token_store(monkeypatch):
    """Replace Redis reset-token storage with an in-memory store."""
    store = {}

    async def fake_store_password_reset_token(token: str, user_id: int) -> None:
        store[token] = user_id

    async def fake_consume_password_reset_token(token: str) -> int | None:
        return store.pop(token, None)

    monkeypatch.setattr(auth, "store_password_reset_token", fake_store_password_reset_token)
    monkeypatch.setattr(auth, "consume_password_reset_token", fake_consume_password_reset_token)
    return store


@pytest.mark.asyncio
async def test_register_generates_email_verification_token(email_outbox):
    """Registration stores an email verification token and sends email."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "verify@example.com",
                "username": "verifyuser",
                "password": "Test1234",
            }
        )

    assert response.status_code == 201

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "verify@example.com"))
        user = result.scalar_one()
        assert user.email_verification_token is not None
        assert user.email_verification_expires_at is not None
        assert user.email_verification_expires_at > utc_now()
        assert user.is_email_verified is False

    assert len(email_outbox) == 1
    assert email_outbox[0]["to"] == "verify@example.com"
    assert user.email_verification_token in email_outbox[0]["html_body"]


@pytest.mark.asyncio
async def test_register_stays_successful_when_email_delivery_raises(
    monkeypatch,
    caplog,
):
    """A post-commit email failure cannot turn registration into a false 500."""

    async def failing_send_email(to: str, subject: str, html_body: str) -> bool:
        raise RuntimeError(f"provider echoed recipient={to} body={html_body}")

    monkeypatch.setattr(auth.email_utils, "send_email", failing_send_email)
    payload = {
        "email": "mail-failure@example.com",
        "username": "mailfailure",
        "password": "Test1234",
    }

    with caplog.at_level(logging.INFO, logger=auth.__name__):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/auth/register", json=payload)
            retry_response = await client.post("/api/v1/auth/register", json=payload)

    assert response.status_code == 201
    assert retry_response.status_code == 400
    assert retry_response.json()["detail"] == "Email already registered"

    async with AsyncSessionLocal() as session:
        result = await session.execute(
            select(User).where(User.email == payload["email"])
        )
        user = result.scalar_one()
        wallet_result = await session.execute(
            select(Wallet).where(Wallet.user_id == user.id)
        )
        assert wallet_result.scalar_one().balance == 0

    log_payload = " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in caplog.records
    )
    assert user.email_verification_token not in log_payload
    assert payload["email"] not in log_payload
    assert any(
        getattr(record, "event", None) == "auth_email_delivery_failed"
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_verify_email_with_valid_token(email_outbox):
    """A valid email verification token verifies the user and clears token."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "valid-token@example.com",
                "username": "validtoken",
                "password": "Test1234",
            }
        )

        async with AsyncSessionLocal() as session:
            result = await session.execute(select(User).where(User.email == "valid-token@example.com"))
            user = result.scalar_one()
            token = user.email_verification_token

        response = await client.get(f"/api/v1/auth/verify-email?token={token}")

    assert response.status_code == 200
    assert response.json()["message"] == "邮箱验证成功"

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "valid-token@example.com"))
        verified_user = result.scalar_one()
        assert verified_user.is_email_verified is True
        assert verified_user.email_verification_token is None
        assert verified_user.email_verification_expires_at is None


@pytest.mark.asyncio
async def test_verify_email_rejects_expired_token():
    """Persisted verification tokens stop working after their deadline."""
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                email="expired-verification@example.com",
                username="expiredverification",
                password_hash="unused-in-this-test",
                email_verification_token="expired-token",
                email_verification_expires_at=utc_now() - timedelta(seconds=1),
            )
        )
        await session.commit()

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get(
            "/api/v1/auth/verify-email?token=expired-token"
        )

    assert response.status_code == 400
    assert response.json()["detail"] == "无效或已过期的验证链接"


@pytest.mark.asyncio
async def test_verify_email_with_invalid_token_returns_400():
    """Invalid email verification tokens are rejected."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.get("/api/v1/auth/verify-email?token=missing")

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_forgot_password_for_unknown_email_returns_success(email_outbox, reset_token_store):
    """Forgot-password response does not reveal whether an email exists."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "unknown@example.com"}
        )

    assert response.status_code == 200
    assert response.json()["message"] == "如果邮箱存在，我们已发送密码重置邮件"
    assert email_outbox == []
    assert reset_token_store == {}


@pytest.mark.asyncio
async def test_forgot_password_hides_email_delivery_failure(
    monkeypatch,
    reset_token_store,
    caplog,
):
    """SMTP failure preserves the generic response and does not log reset tokens."""
    async with AsyncSessionLocal() as session:
        user = User(
            email="forgot-mail-failure@example.com",
            username="forgotmailfailure",
            password_hash="unused-in-this-test",
        )
        session.add(user)
        await session.commit()

    async def failing_send_email(to: str, subject: str, html_body: str) -> bool:
        raise RuntimeError(f"provider echoed recipient={to} body={html_body}")

    monkeypatch.setattr(auth.email_utils, "send_email", failing_send_email)

    with caplog.at_level(logging.INFO, logger=auth.__name__):
        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "forgot-mail-failure@example.com"},
            )

    assert response.status_code == 200
    assert response.json()["message"] == "如果邮箱存在，我们已发送密码重置邮件"
    assert len(reset_token_store) == 1
    token = next(iter(reset_token_store))
    log_payload = " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in caplog.records
    )
    assert token not in log_payload
    assert "forgot-mail-failure@example.com" not in log_payload


@pytest.mark.asyncio
async def test_forgot_password_hides_reset_store_failure(monkeypatch, caplog):
    """A reset-token store outage does not disclose that an account exists."""
    async with AsyncSessionLocal() as session:
        session.add(
            User(
                email="reset-store-failure@example.com",
                username="resetstorefailure",
                password_hash="unused-in-this-test",
            )
        )
        await session.commit()

    attempted_tokens: list[str] = []
    email_called = False

    async def failing_store_password_reset_token(token: str, user_id: int) -> None:
        attempted_tokens.append(token)
        raise auth.RedisError(f"store rejected token={token} user_id={user_id}")

    async def fake_send_email(to: str, subject: str, html_body: str) -> bool:
        nonlocal email_called
        email_called = True
        return True

    monkeypatch.setattr(
        auth,
        "store_password_reset_token",
        failing_store_password_reset_token,
    )
    monkeypatch.setattr(auth.email_utils, "send_email", fake_send_email)

    with caplog.at_level(logging.INFO, logger=auth.__name__):
        async with AsyncClient(app=app, base_url="http://test") as client:
            known_response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "reset-store-failure@example.com"},
            )
            unknown_response = await client.post(
                "/api/v1/auth/forgot-password",
                json={"email": "missing-reset-store@example.com"},
            )

    assert known_response.status_code == unknown_response.status_code == 200
    assert known_response.json() == unknown_response.json()
    assert len(attempted_tokens) == 1
    assert email_called is False
    log_payload = " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in caplog.records
    )
    assert attempted_tokens[0] not in log_payload
    assert "reset-store-failure@example.com" not in log_payload


@pytest.mark.asyncio
async def test_send_email_skips_unconfigured_smtp(monkeypatch, caplog):
    """Local tests and development do not require real SMTP credentials."""
    monkeypatch.setattr(email_utils.settings, "EMAIL_FROM", "")
    monkeypatch.setattr(email_utils.settings, "EMAIL_USERNAME", "")
    monkeypatch.setattr(email_utils.settings, "EMAIL_PASSWORD", "")
    smtp_called = False

    def unexpected_smtp_call(to: str, subject: str, html_body: str) -> None:
        nonlocal smtp_called
        smtp_called = True

    monkeypatch.setattr(email_utils, "_send_email_sync", unexpected_smtp_call)

    with caplog.at_level(logging.INFO, logger=email_utils.__name__):
        delivered = await email_utils.send_email(
            "local@example.com",
            "Local test",
            "<p>token=local-test-secret</p>",
        )

    assert delivered is False
    assert smtp_called is False
    assert "local-test-secret" not in caplog.text
    assert any(
        getattr(record, "event", None) == "email_delivery_skipped"
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_send_email_contains_smtp_failure_without_secret_leak(
    monkeypatch,
    caplog,
):
    """SMTP exceptions become a safe, observable best-effort failure."""
    monkeypatch.setattr(email_utils.settings, "EMAIL_FROM", "sender@example.com")
    monkeypatch.setattr(email_utils.settings, "EMAIL_USERNAME", "smtp-user")
    monkeypatch.setattr(email_utils.settings, "EMAIL_PASSWORD", "smtp-password")

    def failing_smtp_call(to: str, subject: str, html_body: str) -> None:
        raise smtplib.SMTPException(f"provider echoed body={html_body}")

    monkeypatch.setattr(email_utils, "_send_email_sync", failing_smtp_call)

    with caplog.at_level(logging.INFO, logger=email_utils.__name__):
        delivered = await email_utils.send_email(
            "recipient@example.com",
            "Secret-bearing email",
            "<p>token=smtp-secret-token</p>",
        )

    assert delivered is False
    log_payload = " ".join(
        f"{record.getMessage()} {record.__dict__}" for record in caplog.records
    )
    assert "smtp-secret-token" not in log_payload
    assert "recipient@example.com" not in log_payload
    assert any(
        getattr(record, "event", None) == "email_delivery_failed"
        and getattr(record, "error_type", None) == "SMTPException"
        for record in caplog.records
    )


@pytest.mark.asyncio
async def test_reset_password_with_invalid_token_returns_400(reset_token_store):
    """Invalid password reset tokens are rejected."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": "bad-token", "password": "Newpass123"}
        )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_forgot_and_reset_password_updates_password(email_outbox, reset_token_store):
    """A valid reset token updates the user's password."""
    async with AsyncClient(app=app, base_url="http://test") as client:
        await client.post(
            "/api/v1/auth/register",
            json={
                "email": "reset@example.com",
                "username": "resetuser",
                "password": "Test1234",
            }
        )

        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "reset@example.com", "password": "Test1234"},
        )
        previous_access_token = login_response.json()["access_token"]

        forgot_response = await client.post(
            "/api/v1/auth/forgot-password",
            json={"email": "reset@example.com"}
        )

        assert forgot_response.status_code == 200
        assert len(reset_token_store) == 1
        token = next(iter(reset_token_store.keys()))

        reset_response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "password": "Newpass123"}
        )
        replay_response = await client.post(
            "/api/v1/auth/reset-password",
            json={"token": token, "password": "Another123"},
        )
        old_session_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {previous_access_token}"},
        )

    assert reset_response.status_code == 200
    assert reset_response.json()["message"] == "密码重置成功"
    assert replay_response.status_code == 400
    assert old_session_response.status_code == 401
    assert old_session_response.json()["detail"] == "Token 已失效，请重新登录"

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "reset@example.com"))
        user = result.scalar_one()
        assert user.auth_version == 1
        assert verify_password("Newpass123", user.password_hash)
        assert not verify_password("Test1234", user.password_hash)
