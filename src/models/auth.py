from pydantic import BaseModel, Field, EmailStr
from typing import Optional
from datetime import datetime

class UserLogin(BaseModel):
    """Model for user login"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")

class UserRegister(BaseModel):
    """Model for user registration"""
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., min_length=6, description="User password")
    first_name: str = Field(..., min_length=1, max_length=100, description="First name")
    last_name: str = Field(..., min_length=1, max_length=100, description="Last name")
    phone: Optional[str] = Field(None, max_length=20, description="Phone number")
    location: Optional[str] = Field(None, max_length=255, description="Location")

class Token(BaseModel):
    """Model for JWT token response"""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiration time in seconds")
    user_id: int = Field(..., description="User ID")
    email: str = Field(..., description="User email")
    first_name: str = Field(..., description="User first name")

class TokenData(BaseModel):
    """Model for token payload data"""
    user_id: Optional[int] = None
    email: Optional[str] = None
    first_name: Optional[str] = None

class PasswordReset(BaseModel):
    """Model for password reset request"""
    email: EmailStr = Field(..., description="User email")

class PasswordChange(BaseModel):
    """Model for password change"""
    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=6, description="New password")

class AuthResponse(BaseModel):
    """Model for authentication response"""
    success: bool = Field(..., description="Whether the operation was successful")
    message: str = Field(..., description="Response message")
    token: Optional[Token] = Field(None, description="JWT token if login successful")
    user_id: Optional[int] = Field(None, description="User ID if registration successful") 