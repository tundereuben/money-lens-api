from sqlalchemy import CheckConstraint, Column, ForeignKey, Integer, String, Date, DateTime, Float
from sqlalchemy.orm import relationship
from db.session import Base

class Budget(Base):
    __tablename__ = 'budgets'
    __table_args__ = (
        CheckConstraint(
            '(category_id IS NOT NULL) <> (system_category_id IS NOT NULL)',
            name='ck_budgets_one_category_source',
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    amount = Column(Float, nullable=False)
    category_id = Column(Integer, ForeignKey("categories.id"), nullable=True)
    system_category_id = Column(Integer, ForeignKey("system_categories.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime)
    updated_at = Column(DateTime)

    category = relationship("Category", back_populates='budgets')
    system_category = relationship("SystemCategory", back_populates='budgets')
