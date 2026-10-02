from datetime import date as dt_date
from decimal import Decimal
from typing import List, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from models.user import User
from modules.transactions import service as transaction_service
from schemas.category import CategoryType
from schemas.money import MoneyAmount
from schemas.transaction import TransactionResponse
from shared.dependencies import get_current_user, get_db


router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/", response_model=List[TransactionResponse])
def get_transactions(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    transaction_type: Optional[CategoryType] = None,
    start_date: Optional[dt_date] = None,
    end_date: Optional[dt_date] = None,
    category_id: Optional[int] = None,
    min_amount: Optional[MoneyAmount] = None,
    max_amount: Optional[MoneyAmount] = None,
    search: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return transaction_service.get_transactions(
        db,
        current_user.id,
        skip=skip,
        limit=limit,
        transaction_type=transaction_type,
        start_date=start_date,
        end_date=end_date,
        category_id=category_id,
        min_amount=min_amount,
        max_amount=max_amount,
        search=search,
    )