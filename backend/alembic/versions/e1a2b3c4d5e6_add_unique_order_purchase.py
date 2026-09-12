"""add_unique_order_purchase

Revision ID: e1a2b3c4d5e6
Revises: c7d8e9f0a1b2
Create Date: 2026-09-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "e1a2b3c4d5e6"
down_revision = "c7d8e9f0a1b2"
branch_labels = None
depends_on = None


def _remove_duplicate_paid_orders() -> None:
    """Keep one paid order per user/resource before adding uniqueness."""
    bind = op.get_bind()
    rows = bind.execute(
        sa.text(
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
    )

    seen: set[tuple[int, int]] = set()
    duplicate_ids: list[int] = []
    for row in rows:
        key = (row.user_id, row.resource_id)
        if key in seen:
            duplicate_ids.append(row.id)
        else:
            seen.add(key)

    delete_duplicates = sa.text(
        "DELETE FROM orders WHERE id IN :order_ids"
    ).bindparams(sa.bindparam("order_ids", expanding=True))
    for offset in range(0, len(duplicate_ids), 500):
        bind.execute(
            delete_duplicates,
            {"order_ids": duplicate_ids[offset:offset + 500]},
        )


def upgrade() -> None:
    _remove_duplicate_paid_orders()
    op.create_index(
        "uq_orders_paid_user_resource",
        "orders",
        ["user_id", "resource_id"],
        unique=True,
        postgresql_where=sa.text("status = 'PAID'"),
        sqlite_where=sa.text("status = 'PAID'"),
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "uq_orders_paid_user_resource",
        table_name="orders",
        if_exists=True,
    )
