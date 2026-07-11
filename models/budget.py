from sqlalchemy import Column, ForeignKey, Integer, String, Date, DateTime, Float
from sqlalchemy.orm import relationship
from db.session import Base

class Budget(Base):
    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    category = relationship("Category", back_populates='budgets')
