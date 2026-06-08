from pydantic import BaseModel, ConfigDict, EmailStr, Field
from datetime import datetime
from typing import Optional


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=12)  # Strong password requirement


class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    password: Optional[str] = Field(None, min_length=12)


class UserResponse(UserBase):
    id: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime]

    model_config = ConfigDict(from_attributes=True)


class UserDetailResponse(UserResponse):
    """User response with sensitive fields redacted."""

    pass


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshTokenRequest(BaseModel):
    refresh_token: str
