from sqlalchemy import CheckConstraint, Column, Date, ForeignKey, Integer, Numeric, String, text
from sqlalchemy.orm import relationship

from db.session import Base


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "transaction_type IN ('EXPENSE', 'INCOME')",
            name="ck_transactions_transaction_type",
        ),
    )

    id = Column(Integer, primary_key=True, index=True)
    amount = Column(Numeric(14, 2), nullable=False)
    date = Column(Date, nullable=False)
    description = Column(String, nullable=True)
    category_id = Column(Integer, ForeignKey("user_categories.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    transaction_type = Column(
        String(10),
        nullable=False,
        default="EXPENSE",
        server_default=text("'EXPENSE'"),
    )
    time = Column(String, nullable=True)
    payment_method_id = Column(Integer, nullable=True)
    account_id = Column(Integer, nullable=True)
    notes = Column(String, nullable=True)

    user = relationship("User", back_populates="transactions")
    user_category = relationship("UserCategory", back_populates="transactions")