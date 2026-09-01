"""add system category selections

Revision ID: 842c485da76f
Revises: 0da9de5c6377
Create Date: 2026-09-01 10:11:32.269379

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '842c485da76f'
down_revision: Union[str, Sequence[str], None] = '0da9de5c6377'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.alter_column('user_categories', 'category_id', nullable=True)
    op.add_column(
        'user_categories',
        sa.Column('system_category_id', sa.Integer(), nullable=True),
    )
    op.create_foreign_key(
        'fk_user_categories_system_category',
        'user_categories',
        'system_categories',
        ['system_category_id'],
        ['id'],
    )
    op.create_check_constraint(
        'ck_user_categories_one_category_source',
        'user_categories',
        '(category_id IS NOT NULL) <> (system_category_id IS NOT NULL)',
    )
    op.create_index(
        'uq_user_categories_user_category',
        'user_categories',
        ['user_id', 'category_id'],
        unique=True,
        postgresql_where=sa.text('category_id IS NOT NULL'),
    )
    op.create_index(
        'uq_user_categories_user_system_category',
        'user_categories',
        ['user_id', 'system_category_id'],
        unique=True,
        postgresql_where=sa.text('system_category_id IS NOT NULL'),
    )


def downgrade() -> None:
    op.drop_index('uq_user_categories_user_system_category', table_name='user_categories')
    op.drop_index('uq_user_categories_user_category', table_name='user_categories')
    op.drop_constraint('ck_user_categories_one_category_source', 'user_categories')
    op.drop_constraint('fk_user_categories_system_category', 'user_categories', type_='foreignkey')
    op.drop_column('user_categories', 'system_category_id')
    op.alter_column('user_categories', 'category_id', nullable=False)
