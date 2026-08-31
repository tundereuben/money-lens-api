from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from fastapi import HTTPException, status
from typing import Optional
from datetime import date
from models.expense import Expense
from models.category import Category
from models.budget import Budget
from schemas.expense import ExpenseCreate, ExpenseUpdate

def create_expense(db: Session, expense_data: ExpenseCreate, user_id: int):
    # Optional: Verify category exists and belongs to user if needed
    category = db.query(Category).filter(Category.id == expense_data.category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    
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
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None
):
    # query = db.query(Expense).filter(Expense.user_id == user_id)
    query = db.query(Expense).options(
        joinedload(Expense.category)   
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
    
    if "category_id" in update_data:
        category = db.query(Category).filter(Category.id == update_data["category_id"]).first()
        if not category:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")

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

def get_expense_summary(
    db: Session,
    user_id: int,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None
):
    query = db.query(
        Category.id.label("category_id"),
        Category.name.label("category_name"),
        func.sum(Expense.amount).label("total_amount")
    ).join(Expense, Expense.category_id == Category.id).filter(Expense.user_id == user_id)

    if start_date:
        query = query.filter(Expense.date >= start_date)
    if end_date:
        query = query.filter(Expense.date <= end_date)

    category_data = query.group_by(Category.id, Category.name).all()

    expense_query = db.query(Expense).filter(Expense.user_id == user_id)
    
    if start_date:
        expense_query = expense_query.filter(Expense.date >= start_date)

    if end_date:
        expense_query = expense_query.filter(Expense.date <= end_date)

    expenses = expense_query.all()

    expense_map = {}

    for e in expenses:
        expense_map.setdefault(e.category_id, []).append({
            "id": e.id,
            "amount": float(e.amount),
            "date": e.date
        })

    # Fetch all budgets for the user to map them to categories
    budgets = db.query(Budget).filter(Budget.user_id == user_id).all()

    budget_map = {
        b.category_id: {
            "budget_id": b.id,
            "amount": float(b.amount)
        }
        for b in budgets
    }

    total_amount = sum(item.total_amount for item in category_data)

    summaries = []
    for item in category_data:
        budget = budget_map.get(item.category_id, {})
        summaries.append({
            "category_id": item.category_id,
            "category_name": item.category_name,
            "total_amount": float(item.total_amount),
            "percentage": (float(item.total_amount) / total_amount * 100) if total_amount > 0 else 0,
            "budget_id": budget.get("budget_id"),
            "budget": budget.get("amount"),
            "expenses": expense_map.get(item.category_id, [])
        })

    return {
        "total_amount": float(total_amount),
        "categories": summaries
    }
