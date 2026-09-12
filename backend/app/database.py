"""
Database connection and session management.
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy import event, inspect, select
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


def _enable_sqlite_foreign_keys(dbapi_connection, _connection_record) -> None:
    """Enable SQLite foreign-key enforcement for every DBAPI connection."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("PRAGMA foreign_keys=ON")
    finally:
        cursor.close()


if engine.url.get_backend_name() == "sqlite":
    event.listen(engine.sync_engine, "connect", _enable_sqlite_foreign_keys)

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


async def init_db(*, bootstrap_schema: bool | None = None) -> bool:
    """
    Optionally initialize database tables as a local-development fallback.

    Schema mutation is disabled by default. Production and Docker startup must
    use Alembic migrations instead of relying on SQLAlchemy ``create_all`` or
    the compatibility updates below.

    Returns ``True`` only when the explicit schema bootstrap ran.
    """
    enabled = (
        settings.SCHEMA_BOOTSTRAP_ENABLED
        if bootstrap_schema is None
        else bootstrap_schema
    )
    if not enabled:
        return False

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        await conn.run_sync(_run_startup_migrations)

    return True


async def close_db():
    """Close database connection."""
    await engine.dispose()


def _run_startup_migrations(sync_conn) -> None:
    """Apply local compatibility updates when schema bootstrap is enabled."""
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

        existing_indexes = {index["name"] for index in inspector.get_indexes("orders")}
        if "uq_orders_user_resource" in existing_indexes:
            sync_conn.exec_driver_sql("DROP INDEX uq_orders_user_resource")
            existing_indexes.remove("uq_orders_user_resource")

        if "uq_orders_paid_user_resource" not in existing_indexes:
            rows = sync_conn.exec_driver_sql(
                """
                SELECT id, user_id, resource_id
                FROM orders
                WHERE UPPER(CAST(status AS VARCHAR)) = 'PAID'
                ORDER BY
                    user_id,
                    resource_id,
                    created_at DESC,
                    id DESC
                """
            )
            seen: set[tuple[int, int]] = set()
            duplicate_ids: list[int] = []
            for order_id, user_id, resource_id in rows:
                key = (user_id, resource_id)
                if key in seen:
                    duplicate_ids.append(order_id)
                else:
                    seen.add(key)

            for order_id in duplicate_ids:
                sync_conn.exec_driver_sql(
                    "DELETE FROM orders WHERE id = :order_id",
                    {"order_id": order_id},
                )

            sync_conn.exec_driver_sql(
                """
                CREATE UNIQUE INDEX uq_orders_paid_user_resource
                ON orders (user_id, resource_id)
                WHERE status = 'PAID'
                """
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
