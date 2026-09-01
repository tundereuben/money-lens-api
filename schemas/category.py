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
    icon: Optional[str]
    color: Optional[str]

class CategoryCreate(CategoryBase):
    pass

class CategoryUpdate(BaseModel):
    name: Optional[str] = None
    category_type: Optional[CategoryType]
    icon: Optional[str]
    color: Optional[str]


class SystemCategoryResponse(CategoryBase):
    id: int
    icon: str | None = None
    color: str | None = None

    model_config = ConfigDict(from_attributes=True)


class SystemCategoryCreate(CategoryBase):
    icon: str | None = None
    color: str | None = None


class SystemCategoryUpdate(BaseModel):
    name: str | None = None
    category_type: CategoryType | None = None
    icon: str | None = None
    color: str | None = None


class SystemCategorySelectionReplace(BaseModel):
    system_category_ids: list[int]

    @field_validator('system_category_ids')
    @classmethod
    def system_category_ids_must_be_unique(cls, system_category_ids: list[int]):
        if len(system_category_ids) != len(set(system_category_ids)):
            raise ValueError('System category IDs must be unique')
        return system_category_ids


class UserSystemCategoryResponse(BaseModel):
    id: int
    user_id: int
    system_category_id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    system_category: SystemCategoryResponse

    model_config = ConfigDict(from_attributes=True)


class CategoryResponse(CategoryBase):
    id: int
    user_id: int
    icon: str | None = None
    color: str | None = None
    category_type: CategoryType | None = None

    model_config = ConfigDict(from_attributes=True)