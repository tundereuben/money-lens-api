from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, String, Boolean, DateTime, text
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


class SystemCategory(Base):
    __tablename__ = 'system_categories'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=True)
    color = Column(String, nullable=True)
    category_type = Column(String, nullable=False)

    user_categories = relationship('UserCategory', back_populates='system_category')
    expenses = relationship('Expense', back_populates='system_category')
    budgets = relationship('Budget', back_populates='system_category')


class UserCategory(Base):
    __tablename__ = 'user_categories'
    __table_args__ = (
        CheckConstraint(
            '(category_id IS NOT NULL) <> (system_category_id IS NOT NULL)',
            name='ck_user_categories_one_category_source',
        ),
        Index(
            'uq_user_categories_user_category',
            'user_id',
            'category_id',
            unique=True,
            postgresql_where=text('category_id IS NOT NULL'),
        ),
        Index(
            'uq_user_categories_user_system_category',
            'user_id',
            'system_category_id',
            unique=True,
            postgresql_where=text('system_category_id IS NOT NULL'),
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    system_category_id = Column(Integer, ForeignKey('system_categories.id'), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='user_categories')
    category = relationship('Category', back_populates='user_categories')
    system_category = relationship('SystemCategory', back_populates='user_categories')
