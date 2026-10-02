from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from models.budget import Budget
from models.category import UserCategory
from schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse
from schemas.category import CategoryType


def get_active_user_category(
    db: Session,
    user_id: int,
    category_id: int,
):
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
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Active category not found",
        )
    if category.system_category.category_type != CategoryType.EXPENSE.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Budgets require an expense category",
        )
    return category


def create_budget(db: Session, budget_data: BudgetCreate, user_id: int):
    get_active_user_category(db, user_id, budget_data.category_id)

    new_budget = Budget(
        **budget_data.model_dump(),
        user_id = user_id
    )

    db.add(new_budget)
    db.commit()
    db.refresh(new_budget)
    return new_budget


def get_budgets(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    category_id: int | None = None,
):
    query = (
        db.query(Budget)
        .options(joinedload(Budget.user_category).joinedload(UserCategory.system_category))
        .filter(Budget.user_id == user_id)
    )
    if category_id is not None:
        query = query.filter(Budget.category_id == category_id)
    return query.offset(skip).limit(limit).all()


def get_budget(db: Session, budget_id: int, user_id: int):
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget

def update_budget(db: Session, budget_id: int, budget_data: BudgetUpdate, user_id: int):
    budget = get_budget(db, budget_id, user_id)

    update_data = budget_data.model_dump(exclude_unset=True)
    if "category_id" in update_data:
        get_active_user_category(db, user_id, update_data["category_id"])
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