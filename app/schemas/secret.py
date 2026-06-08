from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
from enum import Enum


class SecretType(str, Enum):
    API_KEY = "api_key"
    PASSWORD = "password"
    DATABASE_URL = "database_url"
    TOKEN = "token"
    GENERIC = "generic"


class SecretBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    secret_type: SecretType = SecretType.GENERIC
    description: Optional[str] = Field(None, max_length=1000)


class SecretCreate(SecretBase):
    value: str = Field(..., min_length=1)


class SecretUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    value: Optional[str] = Field(None, min_length=1)
    description: Optional[str] = Field(None, max_length=1000)
    secret_type: Optional[SecretType] = None


class SecretResponse(SecretBase):
    id: str
    created_at: datetime
    updated_at: datetime
    accessed_at: Optional[datetime]
    # Note: value is NOT included in response for security

    class Config:
        from_attributes = True


class SecretValueResponse(SecretResponse):
    """Response that includes the decrypted secret value."""

    value: str


class SecretListResponse(BaseModel):
    total: int
    page: int
    per_page: int
    secrets: list[SecretResponse]
