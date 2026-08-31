from sqlalchemy import Column, ForeignKey, Integer, String, Boolean, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from db.session import Base

class Category(Base):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    icon = Column(String, nullable=True)
    color = Column(String, nullable=True)
    category_type = Column(String)

    user = relationship('User', back_populates='categories')
    user_categories = relationship('UserCategory', back_populates='category', cascade='all, delete-orphan')
    expenses = relationship('Expense', back_populates='category', cascade='all, delete-orphan')
    budgets = relationship("Budget", back_populates="category", cascade="all, delete-orphan")


class UserCategory(Base):
    __tablename__ = 'user_categories'

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='user_categories')
    category = relationship('Category', back_populates='user_categories')
