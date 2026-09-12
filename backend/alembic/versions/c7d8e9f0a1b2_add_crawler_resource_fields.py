"""add crawler source fields to resources

Revision ID: c7d8e9f0a1b2
Revises: b9c1d2e3f4a5
Create Date: 2026-07-29 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "c7d8e9f0a1b2"
down_revision = "b9c1d2e3f4a5"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("resources", sa.Column("source_type", sa.String(length=32), nullable=True))
    op.add_column("resources", sa.Column("source_site", sa.String(length=100), nullable=True))
    op.add_column("resources", sa.Column("source_url", sa.Text(), nullable=True))
    op.add_column("resources", sa.Column("source_external_id", sa.String(length=255), nullable=True))
    op.add_column("resources", sa.Column("source_last_synced_at", sa.DateTime(), nullable=True))
    op.create_index("ix_resources_source_type", "resources", ["source_type"], unique=False)
    op.create_index("ix_resources_source_site", "resources", ["source_site"], unique=False)
    op.create_index("ix_resources_source_external_id", "resources", ["source_external_id"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_resources_source_external_id", table_name="resources")
    op.drop_index("ix_resources_source_site", table_name="resources")
    op.drop_index("ix_resources_source_type", table_name="resources")
    op.drop_column("resources", "source_last_synced_at")
    op.drop_column("resources", "source_external_id")
    op.drop_column("resources", "source_url")
    op.drop_column("resources", "source_site")
    op.drop_column("resources", "source_type")
