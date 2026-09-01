from sqlalchemy.orm import Session, joinedload
from fastapi import HTTPException, status
from models.budget import Budget
from models.category import Category, UserCategory
from schemas.budget import BudgetCreate, BudgetUpdate, BudgetResponse


def validate_budget_category_source(
    db: Session,
    user_id: int,
    category_id: int | None,
    system_category_id: int | None,
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


def create_budget(db: Session, budget_data: BudgetCreate, user_id: int):
    validate_budget_category_source(
        db,
        user_id,
        budget_data.category_id,
        budget_data.system_category_id,
    )

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
    system_category_id: int | None = None,
):
    query = (
        db.query(Budget)
        .options(joinedload(Budget.category), joinedload(Budget.system_category))
        .filter(Budget.user_id == user_id)
    )
    if category_id is not None:
        query = query.filter(Budget.category_id == category_id)
    if system_category_id is not None:
        query = query.filter(Budget.system_category_id == system_category_id)
    return query.offset(skip).limit(limit).all()


def get_budget(db: Session, budget_id: int, user_id: int):
    budget = db.query(Budget).filter(Budget.id == budget_id, Budget.user_id == user_id).first()
    if not budget:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Budget not found")
    return budget

def update_budget(db: Session, budget_id: int, budget_data: BudgetUpdate, user_id: int):
    budget = get_budget(db, budget_id, user_id)

    update_data = budget_data.model_dump(exclude_unset=True)
    if {"category_id", "system_category_id"} & update_data.keys():
        validate_budget_category_source(
            db,
            user_id,
            update_data.get("category_id", budget.category_id),
            update_data.get("system_category_id", budget.system_category_id),
        )
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