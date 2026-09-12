"""restrict category deletes

Revision ID: f2c3d4e5a6b7
Revises: e1a2b3c4d5e6
Create Date: 2026-09-10 00:00:00.000000

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "f2c3d4e5a6b7"
down_revision = "e1a2b3c4d5e6"
branch_labels = None
depends_on = None


_NAMING_CONVENTION = {
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
}


def _find_foreign_key_name(
    table_name: str,
    column_name: str,
    referred_table: str,
) -> str:
    inspector = sa.inspect(op.get_bind())
    matches = [
        foreign_key
        for foreign_key in inspector.get_foreign_keys(table_name)
        if foreign_key["constrained_columns"] == [column_name]
        and foreign_key["referred_table"] == referred_table
    ]
    if len(matches) != 1 or not matches[0].get("name"):
        raise RuntimeError(
            f"Expected one named foreign key for {table_name}.{column_name}"
        )
    return str(matches[0]["name"])


def _replace_category_foreign_key(
    *,
    table_name: str,
    column_name: str,
    constraint_name: str,
    ondelete: str | None,
) -> None:
    bind = op.get_bind()
    if bind.dialect.name == "sqlite":
        # SQLite cannot alter a foreign key in place. The naming convention
        # gives the legacy unnamed constraint a deterministic reflected name.
        with op.batch_alter_table(
            table_name,
            recreate="always",
            naming_convention=_NAMING_CONVENTION,
        ) as batch_op:
            batch_op.drop_constraint(constraint_name, type_="foreignkey")
            batch_op.create_foreign_key(
                constraint_name,
                "categories",
                [column_name],
                ["id"],
                ondelete=ondelete,
            )
        return

    existing_name = _find_foreign_key_name(
        table_name,
        column_name,
        "categories",
    )
    op.drop_constraint(existing_name, table_name, type_="foreignkey")
    op.create_foreign_key(
        constraint_name,
        table_name,
        "categories",
        [column_name],
        ["id"],
        ondelete=ondelete,
    )


def upgrade() -> None:
    _replace_category_foreign_key(
        table_name="categories",
        column_name="parent_id",
        constraint_name="fk_categories_parent_id_categories",
        ondelete="RESTRICT",
    )
    _replace_category_foreign_key(
        table_name="resources",
        column_name="category_id",
        constraint_name="fk_resources_category_id_categories",
        ondelete="RESTRICT",
    )


def downgrade() -> None:
    _replace_category_foreign_key(
        table_name="resources",
        column_name="category_id",
        constraint_name="fk_resources_category_id_categories",
        ondelete=None,
    )
    _replace_category_foreign_key(
        table_name="categories",
        column_name="parent_id",
        constraint_name="fk_categories_parent_id_categories",
        ondelete=None,
    )
