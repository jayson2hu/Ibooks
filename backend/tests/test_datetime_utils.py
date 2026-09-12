"""Regression tests for the backend UTC timestamp contract."""

from datetime import datetime, timezone

import pytest

from app.models.user import User
from app.schemas.responses import ApiResponse, ErrorResponse, PaginatedResponse
from app.utils.datetime_utils import utc_now


def test_utc_now_preserves_naive_database_timestamp_contract():
    before = datetime.now(timezone.utc).replace(tzinfo=None)
    current = utc_now()
    after = datetime.now(timezone.utc).replace(tzinfo=None)

    assert current.tzinfo is None
    assert before <= current <= after


def test_response_timestamps_keep_the_existing_iso_format():
    timestamp = datetime(2026, 9, 10, 3, 30, 45, 123456)

    success = ApiResponse(timestamp=timestamp).model_dump_json()
    error = ErrorResponse(timestamp=timestamp).model_dump_json()
    paginated = PaginatedResponse(
        data=[],
        meta={
            "total": 0,
            "page": 1,
            "page_size": 20,
            "pages": 0,
            "has_next": False,
            "has_prev": False,
        },
        timestamp=timestamp,
    ).model_dump_json()

    expected = '"timestamp":"2026-09-10T03:30:45.123456"'
    assert expected in success
    assert expected in error
    assert expected in paginated


@pytest.mark.asyncio
async def test_sqlalchemy_defaults_remain_naive_utc(db_session):
    user = User(
        email="datetime-contract@example.com",
        username="datetimecontract",
        password_hash="not-used-by-this-test",
    )
    db_session.add(user)
    await db_session.flush()

    assert user.created_at.tzinfo is None
    assert user.updated_at.tzinfo is None

    previous_updated_at = user.updated_at
    user.full_name = "Updated"
    await db_session.flush()

    assert user.updated_at.tzinfo is None
    assert user.updated_at >= previous_updated_at
