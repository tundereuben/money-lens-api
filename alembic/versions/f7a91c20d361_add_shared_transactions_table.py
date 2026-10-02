"""add shared transactions table

Revision ID: f7a91c20d361
Revises: ce30a90f479c
Create Date: 2026-09-28

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f7a91c20d361"
down_revision: Union[str, Sequence[str], None] = "ce30a90f479c"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


INCOME_CATEGORIES = (
    "Salary",
    "Freelance",
    "Business",
    "Investments",
    "Interest",
    "Gifts",
    "Other Income",
)


def upgrade() -> None:
    bind = op.get_bind()
    if sa.inspect(bind).has_table("transactions"):
        existing_transaction_count = bind.execute(
            sa.text("SELECT count(*) FROM transactions")
        ).scalar_one()
        if existing_transaction_count:
            raise RuntimeError(
                "Cannot migrate expenses: transactions already contains rows"
            )
        op.drop_table("transactions")

    op.rename_table("expenses", "transactions")
    op.add_column(
        "transactions",
        sa.Column(
            "transaction_type",
            sa.String(length=10),
            nullable=False,
            server_default="EXPENSE",
        ),
    )
    op.create_check_constraint(
        "ck_transactions_transaction_type",
        "transactions",
        "transaction_type IN ('EXPENSE', 'INCOME')",
    )
    op.execute(sa.text("ALTER INDEX IF EXISTS ix_expenses_id RENAME TO ix_transactions_id"))

    for name in INCOME_CATEGORIES:
        bind.execute(
            sa.text("""
                INSERT INTO system_categories (
                    name, icon, color, category_type, created_by_type,
                    created_by_user_id, created_at, updated_at
                ) VALUES (
                    :name, NULL, NULL, 'INCOME', 'SYSTEM', NULL, NOW(), NOW()
                ) ON CONFLICT (name) DO NOTHING
            """),
            {"name": name},
        )


def downgrade() -> None:
    bind = op.get_bind()
    income_count = bind.execute(
        sa.text("SELECT count(*) FROM transactions WHERE transaction_type = 'INCOME'")
    ).scalar_one()
    if income_count:
        raise RuntimeError("Cannot downgrade while income transactions exist")

    op.drop_constraint(
        "ck_transactions_transaction_type",
        "transactions",
        type_="check",
    )
    op.drop_column("transactions", "transaction_type")
    op.execute(sa.text("ALTER INDEX IF EXISTS ix_transactions_id RENAME TO ix_expenses_id"))
    op.rename_table("transactions", "expenses")