from pydantic import BaseModel, model_validator
from datetime import date
from typing import Optional

from schemas.category import CategoryResponse, SystemCategoryResponse

class BudgetCreate(BaseModel):
    name: str
    amount: float
    category_id: Optional[int] = None
    system_category_id: Optional[int] = None

    @model_validator(mode="after")
    def has_exactly_one_category_source(self):
        if (self.category_id is None) == (self.system_category_id is None):
            raise ValueError("Provide exactly one of category_id or system_category_id")
        return self

class BudgetUpdate(BaseModel):
    name: Optional[str] = None
    amount: Optional[float]
    category_id: Optional[int] = None
    system_category_id: Optional[int] = None
    
class BudgetResponse(BaseModel):
    id: int
    user_id: int
    name: str
    amount: float
    category_id: Optional[int] = None
    system_category_id: Optional[int] = None
    category: Optional[CategoryResponse] = None
    system_category: Optional[SystemCategoryResponse] = None