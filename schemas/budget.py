from pydantic import BaseModel, ConfigDict, field_validator
from decimal import Decimal
from typing import Optional

from schemas.category import UserCategoryResponse
from schemas.money import PositiveMoneyAmount

class BudgetCreate(BaseModel):
    name: str
    amount: PositiveMoneyAmount
    category_id: int

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[PositiveMoneyAmount] = None
    category_id: Optional[int] = None

    @field_validator("name", "amount", "category_id", mode="before")
    @classmethod
    def reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value
    
class BudgetResponse(BaseModel):
    id: int
    user_id: int
    name: str
    amount: Decimal
    category_id: int
    user_category: UserCategoryResponse

    model_config = ConfigDict(from_attributes=True)