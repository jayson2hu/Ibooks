"""add_recharge_packages_and_orders

Revision ID: b9c1d2e3f4a5
Revises: f4d22a62f1bb
Create Date: 2026-04-29 00:00:00.000000

"""
from datetime import datetime, timezone

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b9c1d2e3f4a5'
down_revision = 'f4d22a62f1bb'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'recharge_packages',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('coins', sa.Integer(), nullable=False),
        sa.Column('bonus_coins', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_recharge_packages_id'), 'recharge_packages', ['id'], unique=False)
    op.create_index(op.f('ix_recharge_packages_is_active'), 'recharge_packages', ['is_active'], unique=False)

    op.create_table(
        'recharge_orders',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('recharge_no', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('package_id', sa.Integer(), nullable=True),
        sa.Column('coins', sa.Integer(), nullable=False),
        sa.Column('bonus_coins', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column('payment_method', sa.Enum('ALIPAY', 'WECHAT', name='rechargepaymentmethod'), nullable=False),
        sa.Column('status', sa.Enum('PENDING', 'PAID', 'CANCELLED', 'FAILED', name='rechargeorderstatus'), nullable=False),
        sa.Column('trade_no', sa.String(length=128), nullable=True),
        sa.Column('payment_raw', sa.Text(), nullable=True),
        sa.Column('paid_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['package_id'], ['recharge_packages.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_recharge_orders_id'), 'recharge_orders', ['id'], unique=False)
    op.create_index(op.f('ix_recharge_orders_package_id'), 'recharge_orders', ['package_id'], unique=False)
    op.create_index(op.f('ix_recharge_orders_recharge_no'), 'recharge_orders', ['recharge_no'], unique=True)
    op.create_index(op.f('ix_recharge_orders_status'), 'recharge_orders', ['status'], unique=False)
    op.create_index(op.f('ix_recharge_orders_user_id'), 'recharge_orders', ['user_id'], unique=False)

    recharge_packages = sa.table(
        'recharge_packages',
        sa.column('name', sa.String),
        sa.column('coins', sa.Integer),
        sa.column('bonus_coins', sa.Integer),
        sa.column('amount', sa.Numeric),
        sa.column('is_active', sa.Boolean),
        sa.column('sort_order', sa.Integer),
        sa.column('created_at', sa.DateTime),
        sa.column('updated_at', sa.DateTime),
    )
    now = datetime.now(timezone.utc).replace(tzinfo=None)
    op.bulk_insert(
        recharge_packages,
        [
            {
                'name': '基础充值包',
                'coins': 60,
                'bonus_coins': 0,
                'amount': 6.00,
                'is_active': True,
                'sort_order': 10,
                'created_at': now,
                'updated_at': now,
            },
        ],
    )


def downgrade() -> None:
    op.drop_index(op.f('ix_recharge_orders_user_id'), table_name='recharge_orders')
    op.drop_index(op.f('ix_recharge_orders_status'), table_name='recharge_orders')
    op.drop_index(op.f('ix_recharge_orders_recharge_no'), table_name='recharge_orders')
    op.drop_index(op.f('ix_recharge_orders_package_id'), table_name='recharge_orders')
    op.drop_index(op.f('ix_recharge_orders_id'), table_name='recharge_orders')
    op.drop_table('recharge_orders')
    op.drop_index(op.f('ix_recharge_packages_is_active'), table_name='recharge_packages')
    op.drop_index(op.f('ix_recharge_packages_id'), table_name='recharge_packages')
    op.drop_table('recharge_packages')
