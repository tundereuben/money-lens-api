from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from db.session import Base

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=True)
    email = Column(String, unique=True, index=True, nullable=False)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    hashed_password = Column(String, nullable=False)

    user_categories = relationship('UserCategory', back_populates='user', cascade='all, delete-orphan')
    created_system_categories = relationship('SystemCategory', back_populates='created_by_user')
    transactions = relationship('Transaction', back_populates='user', cascade='all, delete-orphan')
