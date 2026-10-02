from datetime import date as dt_date
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from models.user import User
from modules.incomes import service as income_service
from schemas.income import IncomeCreate, IncomeResponse, IncomeSummaryResponse, IncomeUpdate
from schemas.money import MoneyAmount
from shared.dependencies import get_current_user, get_db


router = APIRouter(prefix="/incomes", tags=["Income"])


@router.get("/summary", response_model=IncomeSummaryResponse)
def get_income_summary(
    start_date: Optional[dt_date] = None,
    end_date: Optional[dt_date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return income_service.get_income_summary(db, current_user.id, start_date, end_date)


@router.post("/", response_model=IncomeResponse, status_code=status.HTTP_201_CREATED)
def create_income(
    income_data: IncomeCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return income_service.create_income(db, income_data, current_user.id)


@router.get("/", response_model=List[IncomeResponse])
def get_incomes(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[dt_date] = None,
    end_date: Optional[dt_date] = None,
    category_id: Optional[int] = None,
    min_amount: Optional[MoneyAmount] = None,
    max_amount: Optional[MoneyAmount] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return income_service.get_incomes(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
    )


@router.get("/{income_id}", response_model=IncomeResponse)
def get_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return income_service.get_income(db, income_id, current_user.id)


@router.patch("/{income_id}", response_model=IncomeResponse)
def update_income(
    income_id: int,
    income_data: IncomeUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return income_service.update_income(db, income_id, income_data, current_user.id)


@router.delete("/{income_id}", status_code=status.HTTP_200_OK)
def delete_income(
    income_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return income_service.delete_income(db, income_id, current_user.id)