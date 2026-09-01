from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from models.category import Category, SystemCategory, UserCategory
from schemas.category import (
    CategoryCreate,
    CategoryUpdate,
    SystemCategoryCreate,
    SystemCategorySelectionReplace,
    SystemCategoryUpdate,
)

def create_category(db: Session, category_data: CategoryCreate, user_id: int):
    new_category = Category(
        **category_data.model_dump(),
        user_id=user_id
    )
    db.add(new_category)
    db.commit()
    db.refresh(new_category)
    return new_category


def get_categories(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return db.query(Category).filter(Category.user_id == user_id).offset(skip).limit(limit).all()


def get_user_categories(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(Category)
        .join(UserCategory, UserCategory.category_id == Category.id)
        .filter(UserCategory.user_id == user_id, UserCategory.is_active.is_(True))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_category(db: Session, category_id: int, user_id: int):
    category = db.query(Category).filter(Category.id == category_id, Category.user_id == user_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Category not found")
    return category

def update_category(db: Session, category_id: int, category_data: CategoryUpdate, user_id: int):
    category = get_category(db, category_id, user_id)
    
    update_data = category_data.model_dump(exclude_unset=True)
    for key, value in update_data.items():
        setattr(category, key, value)
    
    db.commit()
    db.refresh(category)
    return category

def delete_category(db: Session, category_id: int, user_id: int):
    category = get_category(db, category_id, user_id)
    # Note: SQLAlchemy relationship in models/category.py handles cascade delete for expenses
    db.delete(category)
    db.commit()
    return {"message": "Category deleted successfully"}


def get_system_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(SystemCategory).offset(skip).limit(limit).all()


def get_system_category(db: Session, category_id: int):
    category = db.query(SystemCategory).filter(SystemCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System category not found")
    return category


def create_system_category(db: Session, category_data: SystemCategoryCreate):
    category = SystemCategory(**category_data.model_dump())
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_system_category(db: Session, category_id: int, category_data: SystemCategoryUpdate):
    category = get_system_category(db, category_id)
    for key, value in category_data.model_dump(exclude_unset=True).items():
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


def delete_system_category(db: Session, category_id: int):
    category = get_system_category(db, category_id)
    db.delete(category)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="System category cannot be deleted while it is selected or in use",
        )
    return {"message": "System category deleted successfully"}


def get_selected_system_categories(db: Session, user_id: int):
    return (
        db.query(UserCategory)
        .options(joinedload(UserCategory.system_category))
        .filter(
            UserCategory.user_id == user_id,
            UserCategory.system_category_id.isnot(None),
            UserCategory.is_active.is_(True),
        )
        .order_by(UserCategory.system_category_id)
        .all()
    )


def replace_selected_system_categories(
    db: Session,
    user_id: int,
    selection_data: SystemCategorySelectionReplace,
):
    requested_ids = set(selection_data.system_category_ids)
    system_categories = (
        db.query(SystemCategory)
        .filter(SystemCategory.id.in_(requested_ids))
        .all()
        if requested_ids
        else []
    )
    found_ids = {category.id for category in system_categories}
    missing_ids = requested_ids - found_ids
    if missing_ids:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"System categories not found: {sorted(missing_ids)}",
        )

    selections = (
        db.query(UserCategory)
        .filter(
            UserCategory.user_id == user_id,
            UserCategory.system_category_id.isnot(None),
        )
        .all()
    )
    selections_by_system_category_id = {
        selection.system_category_id: selection for selection in selections
    }

    for selection in selections:
        selection.is_active = selection.system_category_id in requested_ids

    for system_category_id in requested_ids:
        if system_category_id not in selections_by_system_category_id:
            db.add(
                UserCategory(
                    user_id=user_id,
                    system_category_id=system_category_id,
                    is_active=True,
                )
            )

    db.commit()
    return get_selected_system_categories(db, user_id)
