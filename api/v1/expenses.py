from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import date as dt_date

from models.category import Category
from shared.dependencies import get_db, get_current_user, get_category_by_id
from schemas.expense import ExpenseCreate, ExpenseUpdate, ExpenseResponse, ExpenseSummaryResponse
from modules.expenses import service as expense_service
from models.user import User

router = APIRouter(prefix="/expenses", tags=["Expenses"])

@router.get("/summary", response_model=ExpenseSummaryResponse)
def get_expense_summary(
    start_date: Optional[dt_date] = None,
    end_date: Optional[dt_date] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    return expense_service.get_expense_summary(db, current_user.id, start_date, end_date)

@router.post("/", response_model=ExpenseResponse, status_code=status.HTTP_201_CREATED)
def create_expense(
    expense_data: ExpenseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expense_service.create_expense(db, expense_data, current_user.id)

@router.get("/", response_model=List[ExpenseResponse])
def get_expenses(
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[dt_date] = None,
    end_date: Optional[dt_date] = None,
    category_id: Optional[int] = None,
    min_amount: Optional[float] = None,
    max_amount: Optional[float] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    
    return expense_service.get_expenses(
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

@router.get("/{expense_id}", response_model=ExpenseResponse)
def get_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expense_service.get_expense(db, expense_id, current_user.id)

@router.patch("/{expense_id}", response_model=ExpenseResponse)
def update_expense(
    expense_id: int,
    expense_data: ExpenseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expense_service.update_expense(db, expense_id, expense_data, current_user.id)

@router.delete("/{expense_id}", status_code=status.HTTP_200_OK)
def delete_expense(
    expense_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return expense_service.delete_expense(db, expense_id, current_user.id)
