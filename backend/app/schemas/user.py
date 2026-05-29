"""
JobPilot — User Schemas
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# --- Request Schemas ---

class UserRegister(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=128)
    full_name: str = Field(..., min_length=1, max_length=255)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        weak_passwords = {
            "123456", "12345678", "123456789", "password", "1234567",
            "qwerty", "admin123", "1234567890", "password123"
        }
        if v.strip() in weak_passwords:
            raise ValueError("Password is too common and weak. Please choose a more secure password.")
        return v


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserUpdate(BaseModel):
    full_name: Optional[str] = Field(None, max_length=255)
    preferences: Optional[dict] = None
    telegram_chat_id: Optional[str] = None


class TokenRefresh(BaseModel):
    refresh_token: str


# --- Response Schemas ---

class UserResponse(BaseModel):
    id: UUID
    email: str
    full_name: str
    role: str
    preferences: Optional[dict] = None
    telegram_chat_id: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    user_id: Optional[str] = None
