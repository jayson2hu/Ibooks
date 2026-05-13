"""
Database connection and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import inspect, select
from sqlalchemy.schema import CreateColumn
from typing import AsyncGenerator
from app.config import settings


# Create async engine
# Create async engine
connect_args = {}
if "sqlite" in settings.DATABASE_URL:
    connect_args = {"check_same_thread": False}
    engine_args = {
        "echo": settings.DB_ECHO,
        "future": True,
        "connect_args": connect_args
    }
else:
    engine_args = {
        "echo": settings.DB_ECHO,
        "future": True,
        "pool_pre_ping": True,
        "pool_size": 10,
        "max_overflow": 20
    }

engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_args
)

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Base class for all database models."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency for getting database session.

    Usage in FastAPI:
        @app.get("/items")
        async def get_items(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db():
    """
    Initialize database tables as a local-development fallback.

    Production and Docker startup should use Alembic migrations instead of
    relying on SQLAlchemy create_all().
    """
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_run_startup_migrations)


async def close_db():
    """Close database connection."""
    await engine.dispose()


def _run_startup_migrations(sync_conn) -> None:
    """Apply lightweight startup migrations for environments not using Alembic."""
    from app.models.resource import Resource
    from app.models.site_settings import SiteSetting
    from app.services.site_settings import CRAWLER_1024_DEFAULT_SETTINGS

    inspector = inspect(sync_conn)
    table_names = set(inspector.get_table_names())

    if "resources" in table_names:
        existing_columns = {column["name"] for column in inspector.get_columns("resources")}
        if "coin_price" not in existing_columns:
            sync_conn.exec_driver_sql(
                "ALTER TABLE resources ADD COLUMN coin_price INTEGER NOT NULL DEFAULT 0"
            )

        for column_name in (
            "source_type",
            "source_site",
            "source_url",
            "source_external_id",
            "source_last_synced_at",
        ):
            if column_name in existing_columns:
                continue

            column = Resource.__table__.c[column_name]
            column_sql = str(CreateColumn(column).compile(dialect=sync_conn.dialect))
            sync_conn.exec_driver_sql(f"ALTER TABLE resources ADD COLUMN {column_sql}")

    if "orders" in table_names:
        existing_columns = {column["name"] for column in inspector.get_columns("orders")}
        if "coin_amount" not in existing_columns:
            sync_conn.exec_driver_sql(
                "ALTER TABLE orders ADD COLUMN coin_amount INTEGER NOT NULL DEFAULT 0"
            )

    if "site_settings" in table_names:
        setting_keys = [item["key"] for item in CRAWLER_1024_DEFAULT_SETTINGS]
        existing_keys = set(
            sync_conn.execute(
                select(SiteSetting.__table__.c.key).where(SiteSetting.__table__.c.key.in_(setting_keys))
            ).scalars()
        )

        for setting in CRAWLER_1024_DEFAULT_SETTINGS:
            if setting["key"] in existing_keys:
                continue

            sync_conn.execute(SiteSetting.__table__.insert().values(**setting))
