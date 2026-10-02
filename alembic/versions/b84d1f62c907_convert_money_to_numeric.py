"""convert monetary amounts to numeric

Revision ID: b84d1f62c907
Revises: f7a91c20d361
Create Date: 2026-09-29

"""
from typing import Sequence, Union

from alembic import context, op
import sqlalchemy as sa


revision: str = "b84d1f62c907"
down_revision: Union[str, Sequence[str], None] = "f7a91c20d361"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


MAX_AMOUNT = "999999999999.99"


def _validate_amounts(table_name: str) -> None:
    bind = op.get_bind()
    invalid_values = f"""
        SELECT count(*)
        FROM {table_name}
        WHERE amount::text IN ('NaN', 'Infinity', '-Infinity')
           OR round(amount::numeric, 2) > {MAX_AMOUNT}::numeric
           OR round(amount::numeric, 2) < -{MAX_AMOUNT}::numeric
    """
    if context.is_offline_mode():
        op.execute(f"""
            DO $$
            BEGIN
                IF EXISTS ({invalid_values.replace('SELECT count(*)', 'SELECT 1')}) THEN
                    RAISE EXCEPTION '{table_name}.amount has non-finite or out-of-range values';
                END IF;
            END;
            $$
        """)
        return

    invalid_count = bind.execute(
        sa.text(invalid_values),
    ).scalar_one()
    if invalid_count:
        raise RuntimeError(
            f"{table_name}.amount has {invalid_count} non-finite or out-of-range values; "
            "audit and correct them before converting to NUMERIC(14, 2)"
        )


def upgrade() -> None:
    for table_name in ("transactions", "budgets"):
        _validate_amounts(table_name)
        op.alter_column(
            table_name,
            "amount",
            existing_type=sa.Float(),
            type_=sa.Numeric(14, 2),
            postgresql_using="round(amount::numeric, 2)",
        )


def downgrade() -> None:
    for table_name in ("budgets", "transactions"):
        op.alter_column(
            table_name,
            "amount",
            existing_type=sa.Numeric(14, 2),
            type_=sa.Float(),
            postgresql_using="amount::double precision",
        )