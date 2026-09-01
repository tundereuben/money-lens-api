from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from shared.dependencies import get_db, get_current_user
from schemas.budget import BudgetCreate, BudgetResponse, BudgetUpdate
from modules.budgets import service as budget_service
from models.user import User

router = APIRouter(prefix='/budgets', tags=['Budgets'])

@router.get("/", response_model=List[BudgetResponse])
def get_budgets(
    skip: int = 0,
    limit: int = 100,
    category_id: int | None = None,
    system_category_id: int | None = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return budget_service.get_budgets(
        db,
        current_user.id,
        skip,
        limit,
        category_id,
        system_category_id,
    )


@router.post("/", response_model=BudgetResponse, status_code=status.HTTP_201_CREATED)
def create_budget(
    budget_data: BudgetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return budget_service.create_budget(db, budget_data, current_user.id)


@router.get("/{budget_id}", response_model=BudgetResponse)
def get_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return budget_service.get_budget(db, budget_id, current_user.id)


@router.patch("/{budget_id}", response_model=BudgetResponse)
def update_budget(
    budget_id: int,
    budget_data: BudgetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return budget_service.update_budget(db, budget_id, budget_data, current_user.id)


@router.delete("/{budget_id}", status_code=status.HTTP_200_OK)
def delete_budget(
    budget_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return budget_service.delete_budget(db, budget_id, current_user.id)