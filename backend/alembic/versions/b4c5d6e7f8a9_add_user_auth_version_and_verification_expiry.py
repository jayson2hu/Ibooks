"""add user auth version and email verification expiry

Revision ID: b4c5d6e7f8a9
Revises: a3b4c5d6e7f8
Create Date: 2026-09-10 17:00:00.000000

"""

from datetime import datetime, timedelta, timezone

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "b4c5d6e7f8a9"
down_revision = "a3b4c5d6e7f8"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column(
            "auth_version",
            sa.Integer(),
            server_default="0",
            nullable=False,
        ),
    )
    op.add_column(
        "users",
        sa.Column("email_verification_expires_at", sa.DateTime(), nullable=True),
    )

    users = sa.table(
        "users",
        sa.column("email_verification_token", sa.String()),
        sa.column("email_verification_expires_at", sa.DateTime()),
    )
    op.execute(
        users.update()
        .where(users.c.email_verification_token.is_not(None))
        .values(
            email_verification_expires_at=datetime.now(timezone.utc).replace(
                tzinfo=None
            )
            + timedelta(hours=24)
        )
    )


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.drop_column("email_verification_expires_at")
        batch_op.drop_column("auth_version")
