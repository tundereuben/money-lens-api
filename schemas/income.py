from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, field_validator

from schemas.category import UserCategoryResponse
from schemas.money import MoneyAmount


class IncomeBase(BaseModel):
    amount: MoneyAmount
    date: date
    time: Optional[str] = None
    description: Optional[str] = None
    category_id: int
    payment_method_id: Optional[int] = None
    account_id: Optional[int] = None
    notes: Optional[str] = None


class IncomeCreate(IncomeBase):
    pass


class IncomeUpdate(BaseModel):
    amount: Optional[MoneyAmount] = None
    date: Optional[date] = None
    time: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[int] = None
    payment_method_id: Optional[int] = None
    account_id: Optional[int] = None
    notes: Optional[str] = None

    @field_validator("amount", "date", "category_id", mode="before")
    @classmethod
    def reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class IncomeResponse(IncomeBase):
    id: int
    user_id: int
    user_category: UserCategoryResponse

    model_config = ConfigDict(from_attributes=True)


class IncomeMini(BaseModel):
    id: int
    amount: Decimal
    date: date

    model_config = ConfigDict(from_attributes=True)


class IncomeCategorySummary(BaseModel):
    category_id: int
    category_name: str
    total_amount: Decimal
    percentage: float
    incomes: list[IncomeMini]


class IncomeSummaryResponse(BaseModel):
    total_income: Decimal
    total_expenses: Decimal
    net_cash_flow: Decimal
    categories: list[IncomeCategorySummary]