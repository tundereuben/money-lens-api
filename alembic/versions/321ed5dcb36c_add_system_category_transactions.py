"""add system category transactions

Revision ID: 321ed5dcb36c
Revises: 842c485da76f
Create Date: 2026-09-01 10:14:34.424363

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '321ed5dcb36c'
down_revision: Union[str, Sequence[str], None] = '842c485da76f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    for table_name, constraint_name in (
        ('expenses', 'ck_expenses_one_category_source'),
        ('budgets', 'ck_budgets_one_category_source'),
    ):
        op.alter_column(table_name, 'category_id', nullable=True)
        op.add_column(
            table_name,
            sa.Column('system_category_id', sa.Integer(), nullable=True),
        )
        op.create_foreign_key(
            f'fk_{table_name}_system_category',
            table_name,
            'system_categories',
            ['system_category_id'],
            ['id'],
        )
        op.create_check_constraint(
            constraint_name,
            table_name,
            '(category_id IS NOT NULL) <> (system_category_id IS NOT NULL)',
        )
        op.create_index(
            f'ix_{table_name}_system_category_id',
            table_name,
            ['system_category_id'],
        )


def downgrade() -> None:
    for table_name, constraint_name in (
        ('budgets', 'ck_budgets_one_category_source'),
        ('expenses', 'ck_expenses_one_category_source'),
    ):
        op.drop_index(f'ix_{table_name}_system_category_id', table_name=table_name)
        op.drop_constraint(constraint_name, table_name)
        op.drop_constraint(
            f'fk_{table_name}_system_category',
            table_name,
            type_='foreignkey',
        )
        op.drop_column(table_name, 'system_category_id')
        op.alter_column(table_name, 'category_id', nullable=False)
