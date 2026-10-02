"""consolidate user categories

Revision ID: cf1d988a0e2f
Revises: 321ed5dcb36c
Create Date: 2026-09-01 10:40:58.796134

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'cf1d988a0e2f'
down_revision: Union[str, Sequence[str], None] = '321ed5dcb36c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()
    miscellaneous_id = bind.execute(
        sa.text("SELECT id FROM system_categories WHERE lower(name) = 'miscellaneous'")
    ).scalar_one_or_none()
    if miscellaneous_id is None:
        raise RuntimeError("The Miscellaneous system category is required for consolidation")

    op.add_column('user_categories', sa.Column('name', sa.String(), nullable=True))
    op.add_column('user_categories', sa.Column('icon', sa.String(), nullable=True))
    op.add_column('user_categories', sa.Column('color', sa.String(), nullable=True))
    op.add_column('user_categories', sa.Column('category_type', sa.String(), nullable=True))

    op.drop_constraint('ck_user_categories_one_category_source', 'user_categories')
    op.drop_index('uq_user_categories_user_category', table_name='user_categories')
    for table_name, check_name in (
        ('expenses', 'ck_expenses_one_category_source'),
        ('budgets', 'ck_budgets_one_category_source'),
    ):
        op.drop_constraint(check_name, table_name)
        op.drop_constraint(f'{table_name}_category_id_fkey', table_name, type_='foreignkey')

    bind.execute(sa.text("""
        INSERT INTO user_categories (user_id, system_category_id, is_active, created_at, updated_at)
        SELECT DISTINCT source.user_id, source.system_category_id, TRUE, NOW(), NOW()
        FROM (
            SELECT c.user_id, COALESCE(sc.id, :miscellaneous_id) AS system_category_id
            FROM categories c
            LEFT JOIN system_categories sc ON lower(sc.name) = lower(c.name)
            UNION
            SELECT e.user_id, e.system_category_id
            FROM expenses e
            WHERE e.system_category_id IS NOT NULL
            UNION
            SELECT b.user_id, b.system_category_id
            FROM budgets b
            WHERE b.system_category_id IS NOT NULL
        ) AS source
        ON CONFLICT (user_id, system_category_id) WHERE system_category_id IS NOT NULL
        DO UPDATE SET is_active = TRUE, updated_at = NOW()
    """), {'miscellaneous_id': miscellaneous_id})

    bind.execute(sa.text("""
        UPDATE expenses AS expense
        SET category_id = user_category.id
        FROM categories AS legacy_category
        LEFT JOIN system_categories AS system_category
            ON lower(system_category.name) = lower(legacy_category.name)
        CROSS JOIN user_categories AS user_category
        WHERE expense.category_id = legacy_category.id
            AND user_category.user_id = expense.user_id
            AND user_category.system_category_id = COALESCE(system_category.id, :miscellaneous_id)
    """), {'miscellaneous_id': miscellaneous_id})
    bind.execute(sa.text("""
        UPDATE expenses AS expense
        SET category_id = user_category.id
        FROM user_categories AS user_category
        WHERE expense.system_category_id IS NOT NULL
            AND user_category.user_id = expense.user_id
            AND user_category.system_category_id = expense.system_category_id
    """))
    bind.execute(sa.text("""
        UPDATE budgets AS budget
        SET category_id = user_category.id
        FROM categories AS legacy_category
        LEFT JOIN system_categories AS system_category
            ON lower(system_category.name) = lower(legacy_category.name)
        CROSS JOIN user_categories AS user_category
        WHERE budget.category_id = legacy_category.id
            AND user_category.user_id = budget.user_id
            AND user_category.system_category_id = COALESCE(system_category.id, :miscellaneous_id)
    """), {'miscellaneous_id': miscellaneous_id})
    bind.execute(sa.text("""
        UPDATE budgets AS budget
        SET category_id = user_category.id
        FROM user_categories AS user_category
        WHERE budget.system_category_id IS NOT NULL
            AND user_category.user_id = budget.user_id
            AND user_category.system_category_id = budget.system_category_id
    """))

    unresolved_expenses = bind.execute(
        sa.text('SELECT count(*) FROM expenses WHERE category_id IS NULL')
    ).scalar_one()
    unresolved_budgets = bind.execute(
        sa.text('SELECT count(*) FROM budgets WHERE category_id IS NULL')
    ).scalar_one()
    if unresolved_expenses or unresolved_budgets:
        raise RuntimeError('Category consolidation left transactions without a user category')

    bind.execute(sa.text('DELETE FROM user_categories WHERE category_id IS NOT NULL'))
    op.drop_constraint(
        'user_categories_category_id_fkey',
        'user_categories',
        type_='foreignkey',
    )
    op.drop_column('user_categories', 'category_id')
    op.create_check_constraint(
        'ck_user_categories_valid_category_kind',
        'user_categories',
        '(system_category_id IS NOT NULL AND name IS NULL AND category_type IS NULL) '
        'OR (system_category_id IS NULL AND name IS NOT NULL AND category_type IS NOT NULL)',
    )
    op.create_index(
        'uq_user_categories_user_custom_name',
        'user_categories',
        ['user_id', sa.text('lower(name)')],
        unique=True,
        postgresql_where=sa.text('system_category_id IS NULL AND name IS NOT NULL'),
    )

    for table_name, check_name in (
        ('expenses', 'ck_expenses_one_category_source'),
        ('budgets', 'ck_budgets_one_category_source'),
    ):
        op.drop_constraint(f'fk_{table_name}_system_category', table_name, type_='foreignkey')
        op.drop_index(f'ix_{table_name}_system_category_id', table_name=table_name)
        op.drop_column(table_name, 'system_category_id')
        op.alter_column(table_name, 'category_id', nullable=False)
        op.create_foreign_key(
            f'fk_{table_name}_user_category',
            table_name,
            'user_categories',
            ['category_id'],
            ['id'],
        )

    op.drop_table('categories')


def downgrade() -> None:
    raise RuntimeError('This data consolidation migration cannot be downgraded safely')
