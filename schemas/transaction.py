from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict

from schemas.category import CategoryType, UserCategoryResponse


class TransactionResponse(BaseModel):
    id: int
    user_id: int
    transaction_type: CategoryType
    amount: Decimal
    date: date
    time: Optional[str] = None
    description: Optional[str] = None
    category_id: int
    payment_method_id: Optional[int] = None
    account_id: Optional[int] = None
    notes: Optional[str] = None
    user_category: UserCategoryResponse

    model_config = ConfigDict(from_attributes=True)