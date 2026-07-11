from enum import Enum
from pydantic import BaseModel, ConfigDict
from typing import Optional


class CategoryType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class CategoryBase(BaseModel):
    name: str
    category_type: CategoryType = CategoryType.EXPENSE
    icon: Optional[str]
    color: Optional[str]

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    category_type: Optional[CategoryType]
    icon: Optional[str]
    color: Optional[str]

class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    icon: str | None = None
    color: str | None = None
    category_type: CategoryType | None = None

    model_config = ConfigDict(from_attributes=True)