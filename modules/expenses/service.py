from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import Optional
from datetime import date
from decimal import Decimal
from models.expense import Expense
from models.category import UserCategory
from models.category import SystemCategory
from models.budget import Budget
from schemas.expense import ExpenseCreate, ExpenseUpdate
from schemas.category import CategoryType


def get_active_user_category(
    db: Session,
    user_id: int,
    category_id: int,
):
    category = (
        db.query(UserCategory)
        .filter(
            UserCategory.user_id == user_id,
            UserCategory.id == category_id,
            UserCategory.is_active.is_(True),
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active category not found",
        )
    if category.system_category.category_type != CategoryType.EXPENSE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category must be an expense category",
        )
    return category


def create_expense(db: Session, expense_data: ExpenseCreate, user_id: int):
    get_active_user_category(db, user_id, expense_data.category_id)

    new_expense = Expense(
        **expense_data.model_dump(),
        user_id=user_id,
        transaction_type=CategoryType.EXPENSE.value,
    )
    db.add(new_expense)
    db.commit()
    db.refresh(new_expense)
    return new_expense

def get_expenses(
    db: Session, 
    user_id: int, 
    skip: int = 0, 
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None
):
    query = db.query(Expense).options(
        joinedload(Expense.user_category).joinedload(UserCategory.system_category),
    ).filter(
        Expense.user_id == user_id,
        Expense.transaction_type == CategoryType.EXPENSE.value,
    ).order_by(
        Expense.date.desc(),
        Expense.id.desc()
    )
    
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if category_id is not None:
        query = query.filter(Expense.category_id == category_id)
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)
    if search:
        query = query.filter(Expense.description.ilike(f"%{search}%"))
        
    return query.offset(skip).limit(limit).all()

def get_expense(db: Session, expense_id: int, user_id: int):
    expense = db.query(Expense).filter(
        Expense.id == expense_id,
        Expense.user_id == user_id,
        Expense.transaction_type == CategoryType.EXPENSE.value,
    ).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense

def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate, user_id: int):
    expense = get_expense(db, expense_id, user_id)
    
    update_data = expense_data.model_dump(exclude_unset=True)
    
    if "category_id" in update_data:
        get_active_user_category(db, user_id, update_data["category_id"])

    for key, value in update_data.items():
        setattr(expense, key, value)
    
    db.commit()
    db.refresh(expense)
    return expense

def delete_expense(db: Session, expense_id: int, user_id: int):
    expense = get_expense(db, expense_id, user_id)
    db.delete(expense)
    db.commit()
    return {"message": "Expense deleted successfully"}


def apply_expense_date_filters(query, start_date: Optional[date], end_date: Optional[date]):
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    return query


def get_expense_summary(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    base_filter = (
        Expense.user_id == user_id,
        Expense.transaction_type == CategoryType.EXPENSE.value,
    )
    grouped_query = apply_expense_date_filters(
        db.query(
            Expense.category_id,
            SystemCategory.name.label("category_name"),
            func.sum(Expense.amount).label("total_amount"),
        )
        .join(UserCategory, Expense.category_id == UserCategory.id)
        .join(SystemCategory, UserCategory.system_category_id == SystemCategory.id)
        .filter(*base_filter)
        .group_by(Expense.category_id, SystemCategory.name),
        start_date,
        end_date,
    )
    category_rows = grouped_query.all()
    category_totals = {row.category_id: row.total_amount for row in category_rows}
    category_names = {row.category_id: row.category_name for row in category_rows}
    total_amount = sum(category_totals.values(), Decimal("0.00"))

    detail_query = apply_expense_date_filters(
        db.query(Expense.category_id, Expense.id, Expense.amount, Expense.date).filter(*base_filter),
        start_date,
        end_date,
    ).order_by(Expense.date.desc(), Expense.id.desc())
    expense_map = {}
    for category_id, expense_id, amount, expense_date in detail_query.all():
        expense_map.setdefault(category_id, []).append({
            "id": expense_id,
            "amount": amount,
            "date": expense_date,
        })

    budgets = db.query(Budget).filter(
        Budget.user_id == user_id,
        Budget.category_id.in_(category_totals),
    ).all() if category_totals else []
    budget_map = {
        budget.category_id: {
            "budget_id": budget.id,
            "amount": budget.amount,
        }
        for budget in budgets
    }
    summaries = []
    for category_id, category_total in category_totals.items():
        budget = budget_map.get(category_id, {})
        summaries.append({
            "category_id": category_id,
            "category_name": category_names[category_id],
            "total_amount": category_total,
            "percentage": float(category_total / total_amount * Decimal("100")) if total_amount else 0,
            "budget_id": budget.get("budget_id"),
            "budget": budget.get("amount"),
            "expenses": expense_map[category_id],
        })

    return {
        "total_amount": total_amount,
        "categories": summaries
    }
