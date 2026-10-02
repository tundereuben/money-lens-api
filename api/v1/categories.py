from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from shared.dependencies import get_db, get_current_user
from schemas.category import (
    SystemCategoryCreate,
    SystemCategorySelectionReplace,
    SystemCategoryResponse,
    SystemCategoryUpdate,
    UserCategoryResponse,
)
from modules.categories import service as category_service
from models.user import User

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.get("/", response_model=List[UserCategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.get_categories(db, current_user.id, skip, limit)


@router.get("/assigned", response_model=List[UserCategoryResponse])
def get_assigned_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.get_user_categories(db, current_user.id, skip, limit)


@router.get("/system", response_model=List[SystemCategoryResponse])
def get_system_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.get_system_categories(db, skip, limit)


@router.get("/system/selected", response_model=List[UserCategoryResponse])
def get_selected_system_categories(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.get_selected_system_categories(db, current_user.id)


@router.put("/system/selected", response_model=List[UserCategoryResponse])
def replace_selected_system_categories(
    selection_data: SystemCategorySelectionReplace,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.replace_selected_system_categories(
        db,
        current_user.id,
        selection_data,
    )


@router.post("/system", response_model=SystemCategoryResponse, status_code=status.HTTP_201_CREATED)
def create_system_category(
    category_data: SystemCategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.create_system_category(db, category_data, current_user.id)


@router.patch("/system/{category_id}", response_model=SystemCategoryResponse)
def update_system_category(
    category_id: int,
    category_data: SystemCategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.update_system_category(
        db,
        category_id,
        category_data,
        current_user.id,
    )


@router.delete("/system/{category_id}", status_code=status.HTTP_200_OK)
def delete_system_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.delete_system_category(db, category_id, current_user.id)


