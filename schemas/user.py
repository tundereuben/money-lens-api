from pydantic import BaseModel, ConfigDict, EmailStr

class UserCreate(BaseModel):
    username: str | None = None
    email: EmailStr
    password: str
    first_name: str | None = None
    last_name: str | None = None

class UserResponse(BaseModel):
    id: int
    username: str | None = None
    email: EmailStr
    first_name: str | None = None
    last_name: str | None = None

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class LoginRequest(BaseModel):
    email: str
    password: str