"""add_daily_signins

Revision ID: f4d22a62f1bb
Revises: 8d7f2b3a91c4
Create Date: 2026-04-28 23:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime, timezone


# revision identifiers, used by Alembic.
revision = 'f4d22a62f1bb'
down_revision = '8d7f2b3a91c4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'daily_signins',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('signin_date', sa.Date(), nullable=False),
        sa.Column('reward_coins', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'signin_date', name='uq_daily_signins_user_date'),
    )
    op.create_index(op.f('ix_daily_signins_id'), 'daily_signins', ['id'], unique=False)
    op.create_index(op.f('ix_daily_signins_signin_date'), 'daily_signins', ['signin_date'], unique=False)
    op.create_index(op.f('ix_daily_signins_user_id'), 'daily_signins', ['user_id'], unique=False)

    site_settings = sa.table(
        'site_settings',
        sa.column('key', sa.String),
        sa.column('value', sa.Text),
        sa.column('category', sa.String),
        sa.column('description', sa.String),
        sa.column('updated_at', sa.DateTime),
        sa.column('updated_by', sa.String),
    )
    op.bulk_insert(
        site_settings,
        [
            {
                'key': 'signin_enabled',
                'value': 'false',
                'category': 'signin',
                'description': '是否开启每日签到奖励',
                'updated_at': datetime.now(timezone.utc).replace(tzinfo=None),
                'updated_by': 'migration',
            },
            {
                'key': 'signin_reward_coins',
                'value': '5',
                'category': 'signin',
                'description': '每日签到奖励书币数量',
                'updated_at': datetime.now(timezone.utc).replace(tzinfo=None),
                'updated_by': 'migration',
            },
        ],
    )


def downgrade() -> None:
    op.execute("DELETE FROM site_settings WHERE key IN ('signin_enabled', 'signin_reward_coins')")
    op.drop_index(op.f('ix_daily_signins_user_id'), table_name='daily_signins')
    op.drop_index(op.f('ix_daily_signins_signin_date'), table_name='daily_signins')
    op.drop_index(op.f('ix_daily_signins_id'), table_name='daily_signins')
    op.drop_table('daily_signins')
