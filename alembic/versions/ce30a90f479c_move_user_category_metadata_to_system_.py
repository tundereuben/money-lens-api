"""move user category metadata to system categories

Revision ID: ce30a90f479c
Revises: cf1d988a0e2f
Create Date: 2026-09-01 11:22:59.065349

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ce30a90f479c'
down_revision: Union[str, Sequence[str], None] = 'cf1d988a0e2f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    bind = op.get_bind()

    op.add_column('system_categories', sa.Column('created_by_type', sa.String(), nullable=True))
    op.add_column('system_categories', sa.Column('created_by_user_id', sa.Integer(), nullable=True))
    op.add_column('system_categories', sa.Column('created_at', sa.DateTime(), nullable=True))
    op.add_column('system_categories', sa.Column('updated_at', sa.DateTime(), nullable=True))
    op.create_foreign_key(
        'fk_system_categories_created_by_user',
        'system_categories',
        'users',
        ['created_by_user_id'],
        ['id'],
    )
    bind.execute(sa.text("""
        UPDATE system_categories
        SET created_by_type = 'SYSTEM', created_at = NOW(), updated_at = NOW()
        WHERE created_by_type IS NULL
    """))

    op.drop_constraint('ck_user_categories_valid_category_kind', 'user_categories')
    op.drop_index('uq_user_categories_user_custom_name', table_name='user_categories')

    bind.execute(sa.text("""
        INSERT INTO system_categories (
            name, icon, color, category_type, created_by_type,
            created_by_user_id, created_at, updated_at
        )
        SELECT DISTINCT ON (lower(user_category.name))
            user_category.name,
            user_category.icon,
            user_category.color,
            user_category.category_type,
            'USER',
            user_category.user_id,
            user_category.created_at,
            user_category.updated_at
        FROM user_categories AS user_category
        WHERE user_category.system_category_id IS NULL
            AND NOT EXISTS (
                SELECT 1
                FROM system_categories AS system_category
                WHERE lower(system_category.name) = lower(user_category.name)
            )
        ORDER BY lower(user_category.name), user_category.id
    """))
    bind.execute(sa.text("""
        UPDATE user_categories AS user_category
        SET system_category_id = system_category.id
        FROM system_categories AS system_category
        WHERE user_category.system_category_id IS NULL
            AND lower(system_category.name) = lower(user_category.name)
    """))

    unresolved_rows = bind.execute(sa.text("""
        SELECT count(*)
        FROM user_categories
        WHERE system_category_id IS NULL
    """)).scalar_one()
    if unresolved_rows:
        raise RuntimeError('User category metadata could not be promoted to system categories')

    duplicate_groups = bind.execute(sa.text("""
        SELECT user_id, system_category_id
        FROM user_categories
        GROUP BY user_id, system_category_id
        HAVING count(*) > 1
    """)).all()
    for user_id, system_category_id in duplicate_groups:
        selection_ids = [
            row[0]
            for row in bind.execute(
                sa.text("""
                    SELECT id
                    FROM user_categories
                    WHERE user_id = :user_id AND system_category_id = :system_category_id
                    ORDER BY id
                """),
                {'user_id': user_id, 'system_category_id': system_category_id},
            )
        ]
        retained_id, duplicate_ids = selection_ids[0], selection_ids[1:]
        bind.execute(
            sa.text('UPDATE expenses SET category_id = :retained_id WHERE category_id = ANY(:duplicate_ids)'),
            {'retained_id': retained_id, 'duplicate_ids': duplicate_ids},
        )
        bind.execute(
            sa.text('UPDATE budgets SET category_id = :retained_id WHERE category_id = ANY(:duplicate_ids)'),
            {'retained_id': retained_id, 'duplicate_ids': duplicate_ids},
        )
        bind.execute(
            sa.text('DELETE FROM user_categories WHERE id = ANY(:duplicate_ids)'),
            {'duplicate_ids': duplicate_ids},
        )

    op.drop_index('uq_user_categories_user_system_category', table_name='user_categories')
    op.drop_column('user_categories', 'name')
    op.drop_column('user_categories', 'icon')
    op.drop_column('user_categories', 'color')
    op.drop_column('user_categories', 'category_type')
    op.alter_column('user_categories', 'system_category_id', nullable=False)
    op.create_unique_constraint(
        'uq_user_categories_user_system_category',
        'user_categories',
        ['user_id', 'system_category_id'],
    )

    op.alter_column('system_categories', 'created_by_type', nullable=False)
    op.alter_column('system_categories', 'created_at', nullable=False)
    op.alter_column('system_categories', 'updated_at', nullable=False)
    op.create_check_constraint(
        'ck_system_categories_creator',
        'system_categories',
        "(created_by_type = 'SYSTEM' AND created_by_user_id IS NULL) OR "
        "(created_by_type = 'USER' AND created_by_user_id IS NOT NULL)",
    )


def downgrade() -> None:
    raise RuntimeError('This category ownership migration cannot be downgraded safely')
