from enum import Enum
from datetime import datetime
from pydantic import BaseModel, ConfigDict
from pydantic import field_validator
from typing import Optional


class CategoryType(str, Enum):
    INCOME = "INCOME"
    EXPENSE = "EXPENSE"

class CategoryBase(BaseModel):
    name: str
    category_type: CategoryType = CategoryType.EXPENSE
    icon: Optional[str] = None
    color: Optional[str] = None

class SystemCategoryResponse(CategoryBase):
    id: int
    icon: str | None = None
    color: str | None = None
    created_by_type: str
    created_by_user_id: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SystemCategoryCreate(CategoryBase):
    icon: str | None = None
    color: str | None = None


class SystemCategoryUpdate(BaseModel):
    name: str | None = None
    category_type: CategoryType | None = None
    icon: str | None = None
    color: str | None = None

    @field_validator("name", "category_type", mode="before")
    @classmethod
    def reject_null_required_fields(cls, value):
        if value is None:
            raise ValueError("Field cannot be null")
        return value


class SystemCategorySelectionReplace(BaseModel):
    system_category_ids: list[int]

    @field_validator('system_category_ids')
    @classmethod
    def system_category_ids_must_be_unique(cls, system_category_ids: list[int]):
        if len(system_category_ids) != len(set(system_category_ids)):
            raise ValueError('System category IDs must be unique')
        return system_category_ids


class UserCategoryResponse(BaseModel):
    id: int
    user_id: int
    system_category_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    system_category: SystemCategoryResponse

    model_config = ConfigDict(from_attributes=True)
