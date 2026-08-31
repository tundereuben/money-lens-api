from pydantic import BaseModel, ConfigDict
from datetime import date
from typing import Optional

from schemas.category import CategoryResponse

class ExpenseBase(BaseModel):
    amount: float
    date: date
    time: Optional[str] = None
    description: Optional[str] = None
    category_id: int
    payment_method_id: Optional[int] = None
    account_id: Optional[int] = None
    notes: Optional[str] = None

class ExpenseCreate(ExpenseBase):
    pass

class ExpenseUpdate(BaseModel):
    amount: Optional[float] = None
    date: Optional[date] = None
    description: Optional[str] = None
    category_id: Optional[int] = None


class ExpenseResponse(ExpenseBase):
    id: int
    user_id: int
    category: CategoryResponse

    model_config = ConfigDict(from_attributes=True)

class ExpenseMini(BaseModel):
    id: int
    amount: float
    date: date

    class Config:
        from_attributes = True


class CategorySummary(BaseModel):
    category_id: int
    category_name: str
    total_amount: float
    percentage: float
    budget: Optional[float] = None
    budget_id: Optional[int] = None
    expenses: list[ExpenseMini]

class ExpenseSummaryResponse(BaseModel):
    total_amount: float
    categories: list[CategorySummary]