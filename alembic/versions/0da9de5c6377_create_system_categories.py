"""create system categories

Revision ID: 0da9de5c6377
Revises: 
Create Date: 2026-09-01 09:41:59.570348

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '0da9de5c6377'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

system_categories = sa.table(
    "system_categories",
    sa.column("name", sa.String),
    sa.column("icon", sa.String),
    sa.column("color", sa.String),
    sa.column("category_type", sa.String),
)

system_category_names = (
    "Utilities",
    "Housing",
    "Food & Groceries",
    "Transportation",
    "Health Care & Medical",
    "Personal & Family Care",
    "Entertainment & Subscriptions",
    "Financial Obligations & Savings",
    "Education & Learning",
    "Shopping & Personal Items",
    "Travel & Accommodation",
    "Work & Business",
    "Giving & Charity",
    "Insurance & Taxes",
    "Miscellaneous",
)


def upgrade() -> None:
    bind = op.get_bind()
    if "system_categories" not in sa.inspect(bind).get_table_names():
        op.create_table(
            "system_categories",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(), nullable=False, unique=True),
            sa.Column("icon", sa.String(), nullable=True),
            sa.Column("color", sa.String(), nullable=True),
            sa.Column("category_type", sa.String(), nullable=False),
        )
        op.create_index("ix_system_categories_id", "system_categories", ["id"])

    existing_names = {
        row[0] for row in bind.execute(sa.select(system_categories.c.name))
    }
    op.bulk_insert(
        system_categories,
        [
            {
                "name": name,
                "icon": None,
                "color": None,
                "category_type": "EXPENSE",
            }
            for name in system_category_names
            if name not in existing_names
        ],
    )


def downgrade() -> None:
    bind = op.get_bind()
    if "system_categories" in sa.inspect(bind).get_table_names():
        op.drop_index("ix_system_categories_id", table_name="system_categories")
        op.drop_table("system_categories")
