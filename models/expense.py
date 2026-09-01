from sqlalchemy import CheckConstraint, Column, Date, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship
from db.session import Base

class Expense(Base):
    __tablename__ = 'expenses'
    __table_args__ = (
        CheckConstraint(
            '(category_id IS NOT NULL) <> (system_category_id IS NOT NULL)',
            name='ck_expenses_one_category_source',
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Float, nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey('categories.id'), nullable=True)
    system_category_id = Column(Integer, ForeignKey('system_categories.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    time = Column(String, nullable=True)
    payment_method_id = Column(Integer, nullable=True)
    account_id = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

    user = relationship('User', back_populates='expenses')
    category = relationship('Category', back_populates='expenses')
    system_category = relationship('SystemCategory', back_populates='expenses')
