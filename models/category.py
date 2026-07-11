from sqlalchemy import Column, ForeignKey, Integer, String
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
    expenses = relationship('Expense', back_populates='category', cascade='all, delete-orphan')
    budgets = relationship("Budget", back_populates="category", cascade="all, delete-orphan")
