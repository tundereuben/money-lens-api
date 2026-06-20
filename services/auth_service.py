from fastapi import HTTPException
from sqlalchemy import or_

from core.security import hash_password, verify_password
from models.user import User


def register_user(db, user_data):
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")

    hashed_password = hash_password(user_data.password)
    new_user = User(
        email=user_data.email,
        username=user_data.username,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        hashed_password=hashed_password,
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user


def authenticate_user(db, identifier: str, password: str):
    user = db.query(User).filter(
        or_(User.email == identifier, User.username == identifier)
    ).first()
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
