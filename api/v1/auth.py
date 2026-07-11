from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordRequestForm

from core.security import create_access_token
from services.auth_service import register_user, authenticate_user
from shared.dependencies import get_db
from schemas.user import LoginRequest, Token, UserCreate, UserResponse

router = APIRouter(prefix="/auth", tags=["Auth"])

@router.post("/register", response_model=UserResponse)
def register(user_create: UserCreate, db: Session = Depends(get_db)):
    return register_user(db, user_create)


@router.post("/login", response_model=Token)
def login(
    login_request: LoginRequest,
    db: Session = Depends(get_db)
):
    user = authenticate_user(
        db,
        login_request.email,
        login_request.password
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
        )

    token = create_access_token(
        data={"sub": user.email}
    )

    return {
        "access_token": token,
        "token_type": "bearer",
    }
