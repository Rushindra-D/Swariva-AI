"""
SWARIVA AI — Authentication Schemas
"""
from typing import Optional
from pydantic import BaseModel, Field


class SignUpRequest(BaseModel):
    email: str = Field(..., pattern=r"^[^@\s]+@[^@\s]+\.[^@\s]+$", description="User email address")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")
    full_name: Optional[str] = Field("Swariva User", description="Display name")
    preferred_language: Optional[str] = Field("auto", description="Primary language")


class SignInRequest(BaseModel):
    email: str = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="Password")


class AuthResponse(BaseModel):
    user_id: str
    email: str
    full_name: str
    preferred_language: str
    access_token: str
    token_type: str = "Bearer"


class UserProfileResponse(BaseModel):
    id: str
    email: Optional[str] = None
    full_name: Optional[str] = None
    preferred_language: Optional[str] = "auto"
    created_at: Optional[str] = None

