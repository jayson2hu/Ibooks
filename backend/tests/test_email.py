"""
Tests for email verification and password reset flows.
"""
import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.v1 import auth
from app.database import AsyncSessionLocal
from app.main import app
from app.models.user import User
from app.utils.security import verify_password


@pytest.fixture
def email_outbox(monkeypatch):
    """Capture outgoing email without sending SMTP messages."""
    messages = []

    async def fake_send_email(to: str, subject: str, html_body: str) -> None:
        messages.append({"to": to, "subject": subject, "html_body": html_body})

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
        assert user.is_email_verified is False

    assert len(email_outbox) == 1
    assert email_outbox[0]["to"] == "verify@example.com"
    assert user.email_verification_token in email_outbox[0]["html_body"]


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

    assert reset_response.status_code == 200
    assert reset_response.json()["message"] == "密码重置成功"

    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == "reset@example.com"))
        user = result.scalar_one()
        assert verify_password("Newpass123", user.password_hash)
        assert not verify_password("Test1234", user.password_hash)
