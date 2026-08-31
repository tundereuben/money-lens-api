from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from typing import List

from shared.dependencies import get_db, get_current_user
from schemas.category import CategoryCreate, CategoryUpdate, CategoryResponse
from modules.categories import service as category_service
from models.user import User

router = APIRouter(prefix="/categories", tags=["Categories"])

@router.get("/", response_model=List[CategoryResponse])
def get_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.get_categories(db, current_user.id, skip, limit)


@router.get("/assigned", response_model=List[CategoryResponse])
def get_assigned_categories(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.get_user_categories(db, current_user.id, skip, limit)


@router.post("/", response_model=CategoryResponse, status_code=status.HTTP_201_CREATED)
def create_category(
    category_data: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.create_category(db, category_data, current_user.id)

@router.get("/{category_id}", response_model=CategoryResponse)
def get_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.get_category(db, category_id, current_user.id)

@router.patch("/{category_id}", response_model=CategoryResponse)
def update_category(
    category_id: int,
    category_data: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.update_category(db, category_id, category_data, current_user.id)

@router.delete("/{category_id}", status_code=status.HTTP_200_OK)
def delete_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return category_service.delete_category(db, category_id, current_user.id)
