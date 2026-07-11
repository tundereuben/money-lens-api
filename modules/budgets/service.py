from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.budget import Budget
from schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse

def create_budget(db: Session, budget_data: BudgetCreate, user_id: int):
    new_budget = Budget(
        **budget_data.model_dump(),
        user_id = user_id
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


def get_budgets(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Budget).filter(Budget.user_id == user_id).offset(skip).limit(limit).all()


def get_budget(db: Session, budget_id: int, user_id: int):
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget

def update_budget(db: Session, budget_id: int, budget_data: BudgetUpdate, user_id: int):
    budget = get_budget(db, budget_id, user_id)

    update_data = budget_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(budget, key, value)

    db.commit()
    db.refresh(budget)
    return budget


def delete_budget(db: Session, budget_id: int, user_id: int):
    budget = get_budget(db, budget_id, user_id)
    db.delete(budget)
    db.commit()
    return { "message": "Budget deleted successfully"}