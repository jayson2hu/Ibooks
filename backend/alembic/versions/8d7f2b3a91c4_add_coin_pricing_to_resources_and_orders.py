"""add_coin_pricing_to_resources_and_orders

Revision ID: 8d7f2b3a91c4
Revises: 51f2d0f4af8a
Create Date: 2026-04-28 22:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8d7f2b3a91c4'
down_revision = '51f2d0f4af8a'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('resources', sa.Column('coin_price', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('orders', sa.Column('coin_amount', sa.Integer(), nullable=False, server_default='0'))

    bind = op.get_bind()
    dialect = bind.dialect.name
    if dialect == 'postgresql':
        op.execute("ALTER TYPE paymentmethod ADD VALUE IF NOT EXISTS 'COIN'")


def downgrade() -> None:
    op.drop_column('orders', 'coin_amount')
    op.drop_column('resources', 'coin_price')
