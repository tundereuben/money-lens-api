from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from models.category import Category
from schemas.category import CategoryCreate, CategoryUpdate

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
