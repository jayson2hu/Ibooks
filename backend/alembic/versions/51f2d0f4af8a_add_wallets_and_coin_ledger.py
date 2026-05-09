"""add_wallets_and_coin_ledger

Revision ID: 51f2d0f4af8a
Revises: a7023eb34c43
Create Date: 2026-04-28 21:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '51f2d0f4af8a'
down_revision = 'a7023eb34c43'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'wallets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('balance', sa.Integer(), nullable=False),
        sa.Column('total_recharged', sa.Integer(), nullable=False),
        sa.Column('total_spent', sa.Integer(), nullable=False),
        sa.Column('total_rewarded', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )
    op.create_index(op.f('ix_wallets_id'), 'wallets', ['id'], unique=False)
    op.create_index(op.f('ix_wallets_user_id'), 'wallets', ['user_id'], unique=True)

    op.create_table(
        'coin_ledger',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('wallet_id', sa.Integer(), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('type', sa.Enum('RECHARGE', 'PURCHASE', 'REFUND', 'SIGNIN', 'ADMIN_ADJUST', name='coinledgertype'), nullable=False),
        sa.Column('related_order_no', sa.String(length=64), nullable=True),
        sa.Column('description', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['wallet_id'], ['wallets.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_coin_ledger_id'), 'coin_ledger', ['id'], unique=False)
    op.create_index(op.f('ix_coin_ledger_related_order_no'), 'coin_ledger', ['related_order_no'], unique=False)
    op.create_index(op.f('ix_coin_ledger_type'), 'coin_ledger', ['type'], unique=False)
    op.create_index(op.f('ix_coin_ledger_user_id'), 'coin_ledger', ['user_id'], unique=False)
    op.create_index(op.f('ix_coin_ledger_wallet_id'), 'coin_ledger', ['wallet_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_coin_ledger_wallet_id'), table_name='coin_ledger')
    op.drop_index(op.f('ix_coin_ledger_user_id'), table_name='coin_ledger')
    op.drop_index(op.f('ix_coin_ledger_type'), table_name='coin_ledger')
    op.drop_index(op.f('ix_coin_ledger_related_order_no'), table_name='coin_ledger')
    op.drop_index(op.f('ix_coin_ledger_id'), table_name='coin_ledger')
    op.drop_table('coin_ledger')
    op.drop_index(op.f('ix_wallets_user_id'), table_name='wallets')
    op.drop_index(op.f('ix_wallets_id'), table_name='wallets')
    op.drop_table('wallets')
