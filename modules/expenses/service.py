from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import Optional
from datetime import date
from models.expense import Expense
from models.category import Category, SystemCategory, UserCategory
from models.budget import Budget
from schemas.expense import ExpenseCreate, ExpenseUpdate


def validate_expense_category_source(
    db: Session,
    user_id: int,
    category_id: Optional[int],
    system_category_id: Optional[int],
):
    if (category_id is None) == (system_category_id is None):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Provide exactly one of category_id or system_category_id",
        )

    if category_id is not None:
        category = (
            db.query(Category)
            .filter(Category.id == category_id, Category.user_id == user_id)
            .first()
        )
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
        return

    selection = (
        db.query(UserCategory)
        .filter(
            UserCategory.user_id == user_id,
            UserCategory.system_category_id == system_category_id,
            UserCategory.is_active.is_(True),
        )
        .first()
    )
    if not selection:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Selected system category not found",
        )


def create_expense(db: Session, expense_data: ExpenseCreate, user_id: int):
    validate_expense_category_source(
        db,
        user_id,
        expense_data.category_id,
        expense_data.system_category_id,
    )

    new_expense = Expense(
        **expense_data.model_dump(),
        user_id=user_id
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
    system_category_id: Optional[int] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None
):
    query = db.query(Expense).options(
        joinedload(Expense.category),
        joinedload(Expense.system_category),
    ).filter(
        Expense.user_id == user_id
    ).order_by(
        Expense.date.desc(),
        Expense.id.desc()
    )
    
    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)
    if category_id:
        query = query.filter(Expense.category_id == category_id)
    if system_category_id:
        query = query.filter(Expense.system_category_id == system_category_id)
    if min_amount is not None:
        query = query.filter(Expense.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Expense.amount <= max_amount)
    if search:
        query = query.filter(Expense.description.ilike(f"%{search}%"))
        
    return query.offset(skip).limit(limit).all()

def get_expense(db: Session, expense_id: int, user_id: int):
    expense = db.query(Expense).filter(Expense.id == expense_id, Expense.user_id == user_id).first()
    if not expense:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Expense not found")
    return expense

def update_expense(db: Session, expense_id: int, expense_data: ExpenseUpdate, user_id: int):
    expense = get_expense(db, expense_id, user_id)
    
    update_data = expense_data.model_dump(exclude_unset=True)
    
    if {"category_id", "system_category_id"} & update_data.keys():
        validate_expense_category_source(
            db,
            user_id,
            update_data.get("category_id", expense.category_id),
            update_data.get("system_category_id", expense.system_category_id),
        )

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
    custom_category_query = db.query(
        Category.id.label("category_id"),
        Category.name.label("category_name"),
        func.sum(Expense.amount).label("total_amount")
    ).join(Expense, Expense.category_id == Category.id).filter(Expense.user_id == user_id)

    custom_category_data = apply_expense_date_filters(
        custom_category_query,
        start_date,
        end_date,
    ).group_by(Category.id, Category.name).all()

    system_category_query = db.query(
        SystemCategory.id.label("system_category_id"),
        SystemCategory.name.label("category_name"),
        func.sum(Expense.amount).label("total_amount"),
    ).join(
        Expense,
        Expense.system_category_id == SystemCategory.id,
    ).filter(Expense.user_id == user_id)

    system_category_data = apply_expense_date_filters(
        system_category_query,
        start_date,
        end_date,
    ).group_by(
        SystemCategory.id,
        SystemCategory.name,
    ).all()

    expenses = apply_expense_date_filters(
        db.query(Expense).filter(Expense.user_id == user_id),
        start_date,
        end_date,
    ).all()

    expense_map = {}

    for e in expenses:
        category_key = (
            "system" if e.system_category_id is not None else "custom",
            e.system_category_id if e.system_category_id is not None else e.category_id,
        )
        expense_map.setdefault(category_key, []).append({
            "id": e.id,
            "amount": float(e.amount),
            "date": e.date
        })

    # Fetch all budgets for the user to map them to categories
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

    budget_map = {
        (
            "system" if b.system_category_id is not None else "custom",
            b.system_category_id if b.system_category_id is not None else b.category_id,
        ): {
            "budget_id": b.id,
            "amount": float(b.amount)
        }
        for b in budgets
    }

    category_data = [
        ("custom", item.category_id, item.category_name, item.total_amount)
        for item in custom_category_data
    ] + [
        ("system", item.system_category_id, item.category_name, item.total_amount)
        for item in system_category_data
    ]

    total_amount = sum(total_amount for _, _, _, total_amount in category_data)

    summaries = []
    for category_source, category_id, category_name, category_total in category_data:
        budget = budget_map.get((category_source, category_id), {})
        summaries.append({
            "category_id": category_id if category_source == "custom" else None,
            "system_category_id": category_id if category_source == "system" else None,
            "category_source": category_source,
            "category_name": category_name,
            "total_amount": float(category_total),
            "percentage": (float(category_total) / total_amount * 100) if total_amount > 0 else 0,
            "budget_id": budget.get("budget_id"),
            "budget": budget.get("amount"),
            "expenses": expense_map.get((category_source, category_id), [])
        })

    return {
        "total_amount": float(total_amount),
        "categories": summaries
    }
