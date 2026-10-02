from datetime import date
from decimal import Decimal
from typing import Optional

from sqlalchemy.orm import Session, joinedload

from models.category import UserCategory
from models.transaction import Transaction
from schemas.category import CategoryType


def get_transactions(
    db: Session,
    user_id: int,
    skip: int = 0,
    limit: int = 100,
    start_date: Optional[date] = None,
    end_date: Optional[date] = None,
    category_id: Optional[int] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    search: Optional[str] = None,
    transaction_type: Optional[CategoryType] = None,
):
    query = (
        db.query(Transaction)
        .options(joinedload(Transaction.user_category).joinedload(UserCategory.system_category))
        .filter(Transaction.user_id == user_id)
        .order_by(Transaction.date.desc(), Transaction.id.desc())
    )
    if transaction_type is not None:
        query = query.filter(Transaction.transaction_type == transaction_type.value)
    if start_date:
        query = query.filter(Transaction.date >= start_date)
    if end_date:
        query = query.filter(Transaction.date <= end_date)
    if category_id is not None:
        query = query.filter(Transaction.category_id == category_id)
    if min_amount is not None:
        query = query.filter(Transaction.amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Transaction.amount <= max_amount)
    if search:
        query = query.filter(Transaction.description.ilike(f"%{search}%"))
    return query.offset(skip).limit(limit).all()