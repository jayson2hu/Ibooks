"""UTC datetime helpers shared by the backend."""

from datetime import datetime, timezone


def utc_now() -> datetime:
    """Return naive UTC compatible with the existing database schema.

    The persisted timestamp columns use SQLAlchemy ``DateTime`` without
    timezone support.  Keeping UTC values naive preserves the current SQLite
    and PostgreSQL representation while avoiding Python's deprecated naive
    UTC constructor.
    """
    return datetime.now(timezone.utc).replace(tzinfo=None)
