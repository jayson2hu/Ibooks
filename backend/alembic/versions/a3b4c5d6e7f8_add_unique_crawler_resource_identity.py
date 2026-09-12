"""add unique crawler resource identity indexes

Revision ID: a3b4c5d6e7f8
Revises: f2c3d4e5a6b7
Create Date: 2026-09-10 14:30:00.000000

"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine import Connection


# revision identifiers, used by Alembic.
revision = "a3b4c5d6e7f8"
down_revision = "f2c3d4e5a6b7"
branch_labels = None
depends_on = None


def _count_duplicate_groups(
    bind: Connection,
    *,
    columns: str,
    predicate: str,
) -> int:
    """Count duplicate identity groups without mutating production data."""
    statement = sa.text(
        f"""
        SELECT COUNT(*)
        FROM (
            SELECT {columns}
            FROM resources
            WHERE {predicate}
            GROUP BY {columns}
            HAVING COUNT(*) > 1
        ) AS duplicate_groups
        """
    )
    return int(bind.execute(statement).scalar_one())


def _assert_no_duplicate_sources(bind: Connection) -> None:
    """Abort with remediation guidance instead of deleting or merging rows."""
    external_id_groups = _count_duplicate_groups(
        bind,
        columns="source_site, source_external_id",
        predicate="source_site IS NOT NULL AND source_external_id IS NOT NULL",
    )
    source_url_groups = _count_duplicate_groups(
        bind,
        columns="source_url",
        predicate="source_url IS NOT NULL",
    )

    if external_id_groups or source_url_groups:
        raise RuntimeError(
            "Cannot add crawler resource uniqueness indexes: found "
            f"{external_id_groups} duplicate (source_site, source_external_id) "
            f"group(s) and {source_url_groups} duplicate source_url group(s). "
            "Resolve the duplicate resources and their references before rerunning "
            "alembic upgrade; this migration will not delete or merge production data."
        )


def upgrade() -> None:
    bind = op.get_bind()
    _assert_no_duplicate_sources(bind)

    external_identity_predicate = sa.text(
        "source_site IS NOT NULL AND source_external_id IS NOT NULL"
    )
    source_url_predicate = sa.text("source_url IS NOT NULL")

    op.create_index(
        "uq_resources_source_site_external_id",
        "resources",
        ["source_site", "source_external_id"],
        unique=True,
        postgresql_where=external_identity_predicate,
        sqlite_where=external_identity_predicate,
    )
    op.create_index(
        "uq_resources_source_url",
        "resources",
        ["source_url"],
        unique=True,
        postgresql_where=source_url_predicate,
        sqlite_where=source_url_predicate,
    )


def downgrade() -> None:
    op.drop_index("uq_resources_source_url", table_name="resources")
    op.drop_index(
        "uq_resources_source_site_external_id",
        table_name="resources",
    )
