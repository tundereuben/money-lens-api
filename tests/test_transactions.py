import os
import json
import unittest
from datetime import date
from decimal import Decimal

os.environ.setdefault("DATABASE_URL", "sqlite://")
os.environ.setdefault("SECRET_KEY", "test-secret")
os.environ.setdefault("ALGORITHM", "HS256")
os.environ.setdefault("OPENAI_API_KEY", "test-key")
os.environ.setdefault("GEMINI_API_KEY", "test-key")

from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

import models.budget
from db.session import Base
from models.category import SystemCategory, UserCategory
from models.user import User
from models.budget import Budget
from models.transaction import Transaction
from modules.categories import service as category_service
from modules.budgets import service as budget_service
from modules.expenses import service as expense_service
from modules.incomes import service as income_service
from modules.transactions import service as transaction_service
from schemas.budget import BudgetCreate, BudgetUpdate
from schemas.category import CategoryType, SystemCategoryUpdate
from schemas.expense import ExpenseCreate, ExpenseUpdate
from schemas.income import IncomeCreate, IncomeUpdate
from schemas.transaction import TransactionResponse


class TransactionServiceTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(self.engine)
        self.db = Session(self.engine)

        user = User(email="person@example.com", hashed_password="hash")
        self.db.add(user)
        self.db.flush()
        self.user_id = user.id

        income_system_category = SystemCategory(name="Salary", category_type="INCOME")
        expense_system_category = SystemCategory(name="Food", category_type="EXPENSE")
        self.db.add_all([income_system_category, expense_system_category])
        self.db.flush()

        income_category = UserCategory(
            user_id=user.id,
            system_category_id=income_system_category.id,
            is_active=True,
        )
        expense_category = UserCategory(
            user_id=user.id,
            system_category_id=expense_system_category.id,
            is_active=True,
        )
        self.db.add_all([income_category, expense_category])
        self.db.commit()
        self.income_category_id = income_category.id
        self.expense_category_id = expense_category.id

    def tearDown(self):
        self.db.close()
        Base.metadata.drop_all(self.engine)
        self.engine.dispose()

    def test_income_and_expenses_are_isolated_and_summary_calculates_net(self):
        income = income_service.create_income(
            self.db,
            IncomeCreate(
                amount=2000,
                date=date(2026, 9, 1),
                category_id=self.income_category_id,
                notes="September salary",
            ),
            self.user_id,
        )
        expense = expense_service.create_expense(
            self.db,
            ExpenseCreate(
                amount=700,
                date=date(2026, 9, 2),
                category_id=self.expense_category_id,
            ),
            self.user_id,
        )

        self.assertEqual(income.transaction_type, "INCOME")
        self.assertEqual(expense.transaction_type, "EXPENSE")
        self.assertEqual([row.id for row in income_service.get_incomes(self.db, self.user_id)], [income.id])
        self.assertEqual([row.id for row in expense_service.get_expenses(self.db, self.user_id)], [expense.id])
        with self.assertRaises(HTTPException) as error:
            income_service.get_income(self.db, expense.id, self.user_id)
        self.assertEqual(error.exception.status_code, 404)

        updated = income_service.update_income(
            self.db,
            income.id,
            IncomeUpdate(amount=2200, notes=None),
            self.user_id,
        )
        self.assertEqual(updated.amount, 2200)
        self.assertIsNone(updated.notes)
        self.assertEqual(updated.date, date(2026, 9, 1))

        summary = income_service.get_income_summary(
            self.db,
            self.user_id,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 30),
        )
        self.assertEqual(summary["total_income"], 2200)
        self.assertEqual(summary["total_expenses"], 700)
        self.assertEqual(summary["net_cash_flow"], 1500)
        self.assertEqual(len(summary["categories"]), 1)

    def test_combined_transactions_include_both_kinds_and_are_user_scoped(self):
        income = income_service.create_income(
            self.db,
            IncomeCreate(
                amount="120.25",
                date=date(2026, 9, 7),
                category_id=self.income_category_id,
            ),
            self.user_id,
        )
        expense = expense_service.create_expense(
            self.db,
            ExpenseCreate(
                amount="40.10",
                date=date(2026, 9, 8),
                category_id=self.expense_category_id,
            ),
            self.user_id,
        )
        other_user = User(email="transactions-other@example.com", hashed_password="hash")
        self.db.add(other_user)
        self.db.flush()
        self.db.add(
            Transaction(
                user_id=other_user.id,
                category_id=self.expense_category_id,
                transaction_type="EXPENSE",
                amount=Decimal("9.00"),
                date=date(2026, 9, 9),
            )
        )
        self.db.commit()

        rows = transaction_service.get_transactions(self.db, self.user_id)
        self.assertEqual({row.id for row in rows}, {income.id, expense.id})
        self.assertEqual({row.transaction_type for row in rows}, {"INCOME", "EXPENSE"})
        responses = [TransactionResponse.model_validate(row) for row in rows]
        self.assertEqual({response.transaction_type.value for response in responses}, {"INCOME", "EXPENSE"})
        self.assertEqual(
            [row.id for row in transaction_service.get_transactions(
                self.db,
                self.user_id,
                transaction_type=CategoryType.INCOME,
            )],
            [income.id],
        )

    def test_each_resource_rejects_the_other_transaction_category_type(self):
        income_data = IncomeCreate(
            amount=100,
            date=date(2026, 9, 1),
            category_id=self.expense_category_id,
        )
        with self.assertRaises(HTTPException) as income_error:
            income_service.create_income(self.db, income_data, self.user_id)
        self.assertEqual(income_error.exception.status_code, 400)

        expense_data = ExpenseCreate(
            amount=100,
            date=date(2026, 9, 1),
            category_id=self.income_category_id,
        )
        with self.assertRaises(HTTPException) as expense_error:
            expense_service.create_expense(self.db, expense_data, self.user_id)
        self.assertEqual(expense_error.exception.status_code, 400)

    def test_expense_partial_update_preserves_expense_kind(self):
        expense = expense_service.create_expense(
            self.db,
            ExpenseCreate(
                amount=50,
                date=date(2026, 9, 3),
                category_id=self.expense_category_id,
            ),
            self.user_id,
        )
        updated = expense_service.update_expense(
            self.db,
            expense.id,
            ExpenseUpdate(amount=75),
            self.user_id,
        )
        self.assertEqual(updated.transaction_type, "EXPENSE")
        self.assertEqual(updated.amount, 75)
        self.assertEqual(updated.date, date(2026, 9, 3))

    def test_category_mutations_are_limited_to_the_owner(self):
        owner_category = SystemCategory(
            name="Owner category",
            category_type="EXPENSE",
            created_by_type="USER",
            created_by_user_id=self.user_id,
        )
        other_user = User(email="other@example.com", hashed_password="hash")
        self.db.add_all([owner_category, other_user])
        self.db.commit()
        self.db.refresh(owner_category)
        self.db.refresh(other_user)

        updated = category_service.update_system_category(
            self.db,
            owner_category.id,
            SystemCategoryUpdate(name="Updated owner category"),
            self.user_id,
        )
        self.assertEqual(updated.name, "Updated owner category")

        unauthorized_update = SystemCategoryUpdate(name="Unauthorized update")
        with self.assertRaises(HTTPException) as update_error:
            category_service.update_system_category(
                self.db,
                owner_category.id,
                unauthorized_update,
                other_user.id,
            )
        self.assertEqual(update_error.exception.status_code, 404)

        with self.assertRaises(HTTPException) as other_delete_error:
            category_service.delete_system_category(
                self.db,
                owner_category.id,
                other_user.id,
            )
        self.assertEqual(other_delete_error.exception.status_code, 404)

        system_update = SystemCategoryUpdate(name="Unauthorized built-in edit")
        with self.assertRaises(HTTPException) as system_update_error:
            category_service.update_system_category(
                self.db,
                self.expense_category_id,
                system_update,
                self.user_id,
            )
        self.assertEqual(system_update_error.exception.status_code, 404)

        with self.assertRaises(HTTPException) as delete_error:
            category_service.delete_system_category(
                self.db,
                self.expense_category_id,
                self.user_id,
            )
        self.assertEqual(delete_error.exception.status_code, 404)

        category_service.delete_system_category(self.db, owner_category.id, self.user_id)
        missing_update = SystemCategoryUpdate(name="Deleted category")
        with self.assertRaises(HTTPException) as missing_error:
            category_service.update_system_category(
                self.db,
                owner_category.id,
                missing_update,
                self.user_id,
            )
        self.assertEqual(missing_error.exception.status_code, 404)

    def test_used_category_type_cannot_change(self):
        custom_transaction_category = SystemCategory(
            name="Transaction category",
            category_type="EXPENSE",
            created_by_type="USER",
            created_by_user_id=self.user_id,
        )
        custom_budget_category = SystemCategory(
            name="Budget category",
            category_type="EXPENSE",
            created_by_type="USER",
            created_by_user_id=self.user_id,
        )
        self.db.add_all([custom_transaction_category, custom_budget_category])
        self.db.flush()
        transaction_user_category = UserCategory(
            user_id=self.user_id,
            system_category_id=custom_transaction_category.id,
            is_active=True,
        )
        budget_user_category = UserCategory(
            user_id=self.user_id,
            system_category_id=custom_budget_category.id,
            is_active=True,
        )
        self.db.add_all([transaction_user_category, budget_user_category])
        self.db.flush()
        self.db.add(
            Transaction(
                amount=40,
                date=date(2026, 9, 3),
                category_id=transaction_user_category.id,
                user_id=self.user_id,
                transaction_type="EXPENSE",
            )
        )
        self.db.add(
            Budget(
                name="Monthly budget",
                amount=300,
                category_id=budget_user_category.id,
                user_id=self.user_id,
            )
        )
        self.db.commit()

        income_update = SystemCategoryUpdate(category_type="INCOME")
        for category in (custom_transaction_category, custom_budget_category):
            with self.subTest(category=category.name):
                with self.assertRaises(HTTPException) as error:
                    category_service.update_system_category(
                        self.db,
                        category.id,
                        income_update,
                        self.user_id,
                    )
                self.assertEqual(error.exception.status_code, 409)
                self.db.rollback()

    def test_patch_schemas_reject_null_required_fields_but_allow_omission(self):
        self.assertEqual(IncomeUpdate().model_dump(exclude_unset=True), {})
        self.assertEqual(ExpenseUpdate().model_dump(exclude_unset=True), {})
        self.assertEqual(BudgetUpdate().model_dump(exclude_unset=True), {})
        self.assertEqual(SystemCategoryUpdate().model_dump(exclude_unset=True), {})

        for schema, field in (
            (IncomeUpdate, "amount"),
            (ExpenseUpdate, "category_id"),
            (BudgetUpdate, "amount"),
            (SystemCategoryUpdate, "name"),
            (SystemCategoryUpdate, "category_type"),
        ):
            with self.subTest(schema=schema.__name__, field=field):
                with self.assertRaises(ValueError):
                    schema(**{field: None})

        self.assertIsNone(IncomeUpdate(notes=None).notes)
        self.assertIsNone(ExpenseUpdate(description=None).description)
        self.assertIsNone(SystemCategoryUpdate(icon=None).icon)

    def test_budgets_only_accept_expense_categories_on_create_and_update(self):
        budget = budget_service.create_budget(
            self.db,
            BudgetCreate(
                name="Food budget",
                amount=300,
                category_id=self.expense_category_id,
            ),
            self.user_id,
        )
        self.assertEqual(budget.category_id, self.expense_category_id)

        income_budget = BudgetUpdate(category_id=self.income_category_id)
        with self.assertRaises(HTTPException) as update_error:
            budget_service.update_budget(self.db, budget.id, income_budget, self.user_id)
        self.assertEqual(update_error.exception.status_code, 400)

        income_budget_create = BudgetCreate(
            name="Invalid budget",
            amount=100,
            category_id=self.income_category_id,
        )
        with self.assertRaises(HTTPException) as create_error:
            budget_service.create_budget(self.db, income_budget_create, self.user_id)
        self.assertEqual(create_error.exception.status_code, 400)

    def test_money_uses_exact_cents_and_allows_signed_adjustments(self):
        first_income = IncomeCreate(
            amount="0.10",
            date=date(2026, 9, 4),
            category_id=self.income_category_id,
        )
        second_income = IncomeCreate(
            amount="0.20",
            date=date(2026, 9, 5),
            category_id=self.income_category_id,
        )
        negative_expense = ExpenseCreate(
            amount="-0.05",
            date=date(2026, 9, 5),
            category_id=self.expense_category_id,
        )
        income_service.create_income(self.db, first_income, self.user_id)
        income_service.create_income(self.db, second_income, self.user_id)
        expense_service.create_expense(self.db, negative_expense, self.user_id)

        summary = income_service.get_income_summary(self.db, self.user_id)
        self.assertEqual(summary["total_income"], Decimal("0.30"))
        self.assertEqual(summary["total_expenses"], Decimal("-0.05"))
        self.assertEqual(summary["net_cash_flow"], Decimal("0.35"))
        self.assertEqual(summary["categories"][0]["incomes"][0]["amount"], Decimal("0.20"))

        expense_summary = expense_service.get_expense_summary(self.db, self.user_id)
        self.assertEqual(expense_summary["total_amount"], Decimal("-0.05"))
        self.assertEqual(expense_summary["categories"][0]["total_amount"], Decimal("-0.05"))
        self.assertEqual(expense_summary["categories"][0]["expenses"][0]["amount"], Decimal("-0.05"))

        budget = budget_service.create_budget(
            self.db,
            BudgetCreate(name="Cents budget", amount="1.25", category_id=self.expense_category_id),
            self.user_id,
        )
        self.assertEqual(budget.amount, Decimal("1.25"))
        self.assertEqual(json.loads(first_income.model_dump_json())["amount"], "0.10")

    def test_money_schemas_reject_extra_precision_nonfinite_and_nonpositive_budgets(self):
        for amount in ("1.001", "NaN", "Infinity", "1000000000000.00"):
            invalid_income = {
                "amount": amount,
                "date": date(2026, 9, 1),
                "category_id": self.income_category_id,
            }
            with self.subTest(amount=amount):
                with self.assertRaises(ValueError):
                    IncomeCreate(**invalid_income)

        for amount in ("0.00", "-0.01"):
            invalid_budget = {
                "name": "Invalid amount",
                "amount": amount,
                "category_id": self.expense_category_id,
            }
            with self.subTest(budget_amount=amount):
                with self.assertRaises(ValueError):
                    BudgetCreate(**invalid_budget)


if __name__ == "__main__":
    unittest.main()