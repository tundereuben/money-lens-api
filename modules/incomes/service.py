from datetime import date
from decimal import Decimal
from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import func
from sqlalchemy.orm import Session, joinedload

from models.category import UserCategory
from models.category import SystemCategory
from models.transaction import Transaction
from schemas.category import CategoryType
from schemas.income import IncomeCreate, IncomeUpdate


def _get_active_income_category(db: Session, user_id: int, category_id: int):
    category = (
        db.query(UserCategory)
        .options(joinedload(UserCategory.system_category))
        .filter(
            UserCategory.user_id == user_id,
            UserCategory.id == category_id,
            UserCategory.is_active.is_(True),
        )
        .first()
    )
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Active category not found")
    if category.system_category.category_type != CategoryType.INCOME.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category must be an income category",
        )
    return category


def create_income(db: Session, income_data: IncomeCreate, user_id: int):
    _get_active_income_category(db, user_id, income_data.category_id)
    income = Transaction(
        **income_data.model_dump(),
        user_id=user_id,
        transaction_type=CategoryType.INCOME.value,
    )
    db.add(income)
    db.commit()
    db.refresh(income)
    return income


def get_incomes(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
):
    query = (
        db.query(Transaction)
        .options(joinedload(Transaction.user_category).joinedload(UserCategory.system_category))
        .filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == CategoryType.INCOME.value,
        )
        .order_by(Transaction.date.desc(), Transaction.id.desc())
    )
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()


def get_income(db: Session, income_id: int, user_id: int):
    income = (
        db.query(Transaction)
        .filter(
            Transaction.id == income_id,
            Transaction.user_id == user_id,
            Transaction.transaction_type == CategoryType.INCOME.value,
        )
        .first()
    )
    if not income:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Income not found")
    return income


def update_income(db: Session, income_id: int, income_data: IncomeUpdate, user_id: int):
    income = get_income(db, income_id, user_id)
    update_data = income_data.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        _get_active_income_category(db, user_id, update_data["category_id"])
    for key, value in update_data.items():
        setattr(income, key, value)
    db.commit()
    db.refresh(income)
    return income


def delete_income(db: Session, income_id: int, user_id: int):
    income = get_income(db, income_id, user_id)
    db.delete(income)
    db.commit()
    return {"message": "Income deleted successfully"}


def get_income_summary(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
):
    income_filter = (
        Transaction.user_id == user_id,
        Transaction.transaction_type == CategoryType.INCOME.value,
    )
    expense_filter = (
        Transaction.user_id == user_id,
        Transaction.transaction_type == CategoryType.EXPENSE.value,
    )
    income_totals_query = db.query(
        Transaction.category_id,
        SystemCategory.name.label("category_name"),
        func.sum(Transaction.amount).label("total_amount"),
    ).join(
        UserCategory, Transaction.category_id == UserCategory.id
    ).join(
        SystemCategory, UserCategory.system_category_id == SystemCategory.id
    ).filter(
        *income_filter
    )
    expense_total_query = db.query(func.coalesce(func.sum(Transaction.amount), 0)).filter(*expense_filter)
    if start_date:
        income_totals_query = income_totals_query.filter(Transaction.date >= start_date)
        expense_total_query = expense_total_query.filter(Transaction.date >= start_date)
    if end_date:
        income_totals_query = income_totals_query.filter(Transaction.date <= end_date)
        expense_total_query = expense_total_query.filter(Transaction.date <= end_date)

    grouped_rows = income_totals_query.group_by(
        Transaction.category_id,
        SystemCategory.name,
    ).all()
    category_totals = {row.category_id: row.total_amount for row in grouped_rows}
    category_names = {row.category_id: row.category_name for row in grouped_rows}
    total_income = sum(category_totals.values(), Decimal("0.00"))
    total_expenses = expense_total_query.scalar() or Decimal("0.00")

    detail_query = db.query(
        Transaction.category_id,
        Transaction.id,
        Transaction.amount,
        Transaction.date,
    ).filter(*income_filter)
    if start_date:
        detail_query = detail_query.filter(Transaction.date >= start_date)
    if end_date:
        detail_query = detail_query.filter(Transaction.date <= end_date)
    category_incomes: dict[int, list[dict[str, object]]] = {}
    for category_id, income_id, amount, income_date in detail_query.order_by(
        Transaction.date.desc(),
        Transaction.id.desc(),
    ).all():
        category_incomes.setdefault(category_id, []).append({
            "id": income_id,
            "amount": amount,
            "date": income_date,
        })

    categories = [
        {
            "category_id": category_id,
            "category_name": category_names[category_id],
            "total_amount": category_total,
            "percentage": float(category_total / total_income * Decimal("100")) if total_income else 0,
            "incomes": category_incomes[category_id],
        }
        for category_id, category_total in category_totals.items()
    ]
    return {
        "total_income": total_income,
        "total_expenses": total_expenses,
        "net_cash_flow": total_income - total_expenses,
        "categories": categories,
    }