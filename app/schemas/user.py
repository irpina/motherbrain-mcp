"""User schemas for RBAC.
"""
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, ConfigDict


class UserCreate(BaseModel):
    """Schema for creating a new user."""
    name: str
    email: Optional[str] = None
    role: str = "user"  # "admin" | "user"


class UserResponse(BaseModel):
    """Schema for user response (token excluded)."""
    user_id: str
    name: str
    email: Optional[str]
    role: str
    is_active: bool
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class UserRegistrationResponse(UserResponse):
    """Schema for user creation response — includes the plaintext token (shown once)."""
    token: str


class UserUpdate(BaseModel):
    """Schema for updating a user."""
    name: Optional[str] = None
    email: Optional[str] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None
