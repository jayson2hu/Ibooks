"""Security utility contract tests."""

from datetime import datetime, timedelta, timezone

import jwt

from app.config import settings
from app.utils import security


LEGACY_PYTHON_JOSE_TOKEN = (
    "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9."
    "eyJzdWIiOiI0MiIsImVtYWlsIjoibGVnYWN5QGV4YW1wbGUuY29tIiwicm9sZSI6InVzZXIiLCJpYXQiOjE3MDQwNjcyMDAsImV4cCI6NDEwMjQ0NDgwMH0."
    "kqQe5_u8cDg2kB2hjPrNb6zlBu2U5AFXWnXkS93o-B0"
)
CONTRACT_SECRET = "contract-secret-key-that-is-long-enough"


def test_create_access_token_preserves_claim_contract(monkeypatch):
    """PyJWT emits the same HS256 header and claims used by existing clients."""
    fixed_now = datetime(2026, 9, 10, 12, 0, 0)
    monkeypatch.setattr(security, "utc_now", lambda: fixed_now)
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", CONTRACT_SECRET)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256")

    token = security.create_access_token(
        {"sub": 42, "email": "user@example.com", "role": "user"},
        expires_delta=timedelta(minutes=15),
    )

    assert jwt.get_unverified_header(token) == {"alg": "HS256", "typ": "JWT"}
    payload = jwt.decode(
        token,
        CONTRACT_SECRET,
        algorithms=["HS256"],
        options={"verify_exp": False, "verify_iat": False},
    )
    issued_at = int(fixed_now.replace(tzinfo=timezone.utc).timestamp())
    jti = payload.pop("jti")
    assert isinstance(jti, str) and jti
    assert payload == {
        "sub": "42",
        "email": "user@example.com",
        "role": "user",
        "exp": issued_at + 900,
        "iat": issued_at,
        "typ": "access",
    }


def test_decode_access_token_accepts_existing_python_jose_token(monkeypatch):
    """Tokens issued before the library migration remain valid until expiry."""
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", CONTRACT_SECRET)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256")

    payload = security.decode_access_token(LEGACY_PYTHON_JOSE_TOKEN)

    assert payload is not None
    assert payload["sub"] == "42"
    assert payload["email"] == "legacy@example.com"
    assert payload["role"] == "user"


def test_decode_access_token_rejects_expired_and_wrongly_signed_tokens(monkeypatch):
    """Expiration and signature verification remain fail-closed."""
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", CONTRACT_SECRET)
    monkeypatch.setattr(settings, "JWT_ALGORITHM", "HS256")
    expired = jwt.encode(
        {"sub": "42", "exp": datetime(2020, 1, 1, tzinfo=timezone.utc)},
        CONTRACT_SECRET,
        algorithm="HS256",
    )
    wrong_signature = jwt.encode(
        {"sub": "42", "exp": datetime(2100, 1, 1, tzinfo=timezone.utc)},
        "a-different-signing-secret-that-is-long-enough",
        algorithm="HS256",
    )

    assert security.decode_access_token(expired) is None
    assert security.decode_access_token(wrong_signature) is None
