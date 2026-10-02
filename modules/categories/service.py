from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, status
from models.category import SystemCategory, UserCategory
from models.budget import Budget
from models.transaction import Transaction
from schemas.category import (
    SystemCategoryCreate,
    SystemCategorySelectionReplace,
    SystemCategoryUpdate,
)

def get_categories(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return (
        db.query(UserCategory)
        .options(joinedload(UserCategory.system_category))
        .filter(UserCategory.user_id == user_id, UserCategory.is_active.is_(True))
        .offset(skip)
        .limit(limit)
        .all()
    )


def get_user_categories(db: Session, user_id: int, skip: int = 0, limit: int = 100):
    return get_categories(db, user_id, skip, limit)


def get_system_categories(db: Session, skip: int = 0, limit: int = 100):
    return db.query(SystemCategory).offset(skip).limit(limit).all()


def get_system_category(db: Session, category_id: int):
    category = db.query(SystemCategory).filter(SystemCategory.id == category_id).first()
    if not category:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="System category not found")
    return category


def get_owned_system_category(db: Session, category_id: int, user_id: int):
    category = (
        db.query(SystemCategory)
        .filter(
            SystemCategory.id == category_id,
            SystemCategory.created_by_type == "USER",
            SystemCategory.created_by_user_id == user_id,
        )
        .first()
    )
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="System category not found",
        )
    return category


def create_system_category(db: Session, category_data: SystemCategoryCreate, user_id: int):
    category = SystemCategory(
        **category_data.model_dump(),
        created_by_type='USER',
        created_by_user_id=user_id,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_system_category(
    db: Session,
    category_id: int,
    category_data: SystemCategoryUpdate,
    user_id: int,
):
    category = get_owned_system_category(db, category_id, user_id)
    update_data = category_data.model_dump(exclude_unset=True)
    new_category_type = update_data.get("category_type")
    if "category_type" in update_data and new_category_type is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Category type cannot be null",
        )
    if new_category_type and new_category_type.value != category.category_type:
        transaction_in_use = (
            db.query(Transaction.id)
            .join(UserCategory, Transaction.category_id == UserCategory.id)
            .filter(UserCategory.system_category_id == category_id)
            .first()
        )
        budget_in_use = (
            db.query(Budget.id)
            .join(UserCategory, Budget.category_id == UserCategory.id)
            .filter(UserCategory.system_category_id == category_id)
            .first()
        )
        if transaction_in_use or budget_in_use:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Category type cannot change while the category is in use",
            )

    for key, value in update_data.items():
        if key == "category_type" and value is not None:
            value = value.value
        setattr(category, key, value)
    db.commit()
    db.refresh(category)
    return category


def delete_system_category(db: Session, category_id: int, user_id: int):
    category = get_owned_system_category(db, category_id, user_id)
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
