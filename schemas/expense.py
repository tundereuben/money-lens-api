from pydantic import BaseModel, ConfigDict, model_validator
from datetime import date
from typing import Optional

from schemas.category import CategoryResponse, SystemCategoryResponse

class ExpenseBase(BaseModel):
    amount: float
    date: date
    time: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    system_category_id: Optional[int] = None
    payment_method_id: Optional[int] = None
    account_id: Optional[int] = None
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    @model_validator(mode="after")
    def has_exactly_one_category_source(self):
        if (self.category_id is None) == (self.system_category_id is None):
            raise ValueError("Provide exactly one of category_id or system_category_id")
        return self

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    date: Optional[date] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    system_category_id: Optional[int] = None


class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    category: Optional[CategoryResponse] = None
    system_category: Optional[SystemCategoryResponse] = None

    model_config = ConfigDict(from_attributes=True)

class ExpenseMini(BaseModel):
    id: int
    amount: float
    date: date

    class Config:
        from_attributes = True


class CategorySummary(BaseModel):
    category_id: Optional[int] = None
    system_category_id: Optional[int] = None
    category_source: str
    category_name: str
    total_amount: float
    percentage: float
    budget: Optional[float] = None
    budget_id: Optional[int] = None
    expenses: list[ExpenseMini]

class ExpenseSummaryResponse(BaseModel):
    total_amount: float
    categories: list[CategorySummary]