from sqlalchemy import CheckConstraint, Column, ForeignKey, Index, Integer, String, Boolean, DateTime
from datetime import datetime
from sqlalchemy.orm import relationship
from db.session import Base

class SystemCategory(Base):
    __tablename__ = 'system_categories'
    __table_args__ = (
        CheckConstraint(
            "(created_by_type = 'SYSTEM' AND created_by_user_id IS NULL) OR "
            "(created_by_type = 'USER' AND created_by_user_id IS NOT NULL)",
            name='ck_system_categories_creator',
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False)
    icon = Column(String, nullable=True)
    color = Column(String, nullable=True)
    category_type = Column(String, nullable=False)
    created_by_type = Column(String, nullable=False, default='SYSTEM')
    created_by_user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    user_categories = relationship('UserCategory', back_populates='system_category')
    created_by_user = relationship('User', back_populates='created_system_categories')


class UserCategory(Base):
    __tablename__ = 'user_categories'
    __table_args__ = (
        Index(
            'uq_user_categories_user_system_category',
            'user_id',
            'system_category_id',
            unique=True,
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    system_category_id = Column(Integer, ForeignKey('system_categories.id'), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = relationship('User', back_populates='user_categories')
    system_category = relationship('SystemCategory', back_populates='user_categories')
    transactions = relationship('Transaction', back_populates='user_category')
    budgets = relationship('Budget', back_populates='user_category')
