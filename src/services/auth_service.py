import os
import logging
import secrets
import hashlib
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from supabase import create_client, Client

from src.models.auth import UserLogin, UserRegister, Token, TokenData, AuthResponse
from src.models.user_profile import User, UserCreate
from src.core.config import get_settings

logger = logging.getLogger(__name__)

class AuthService:
    """Service for user authentication, registration, and JWT token management"""
    
    def __init__(self):
        settings = get_settings()
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_anon_key
        self.supabase: Optional[Client] = None
        
        # JWT Configuration
        self.secret_key = settings.secret_key or "your-secret-key-change-in-production"
        self.algorithm = "HS256"
        self.access_token_expire_minutes = 30
        
        # Password hashing
        self.pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        
    async def initialize(self):
        """Initialize Supabase client"""
        try:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and key must be set")
            
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            logger.info("Auth service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing auth service: {e}")
            raise
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return self.pwd_context.verify(plain_password, hashed_password)
    
    def get_password_hash(self, password: str) -> str:
        """Hash a password"""
        return self.pwd_context.hash(password)
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token"""
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=self.access_token_expire_minutes)
        
        to_encode.update({"exp": expire})
        encoded_jwt = jwt.encode(to_encode, self.secret_key, algorithm=self.algorithm)
        return encoded_jwt
    
    def verify_token(self, token: str) -> Optional[TokenData]:
        """Verify and decode a JWT token"""
        try:
            payload = jwt.decode(token, self.secret_key, algorithms=[self.algorithm])
            user_id: int = payload.get("user_id")
            email: str = payload.get("email")
            first_name: str = payload.get("first_name")
            
            if user_id is None or email is None or first_name is None:
                return None
            
            return TokenData(user_id=user_id, email=email, first_name=first_name)
        except JWTError:
            return None
    
    async def register_user(self, user_data: UserRegister) -> AuthResponse:
        """Register a new user with password hashing"""
        try:
            # Check if user already exists
            existing_user = await self.get_user_by_email(user_data.email)
            if existing_user:
                return AuthResponse(
                    success=False,
                    message="User with this email already exists"
                )
            
            # Hash the password
            hashed_password = self.get_password_hash(user_data.password)
            
            # Create user data for database
            user_create_data = UserCreate(
                email=user_data.email,
                first_name=user_data.first_name,
                last_name=user_data.last_name,
                phone=user_data.phone,
                location=user_data.location
            )
            
            # Insert user into database with hashed password
            user_dict = user_create_data.model_dump()
            user_dict["password_hash"] = hashed_password
            
            result = self.supabase.table("users").insert(user_dict).execute()
            
            if not result.data:
                return AuthResponse(
                    success=False,
                    message="Failed to create user"
                )
            
            user = User(**result.data[0])
            
            return AuthResponse(
                success=True,
                message="User registered successfully",
                user_id=user.id
            )
            
        except Exception as e:
            logger.error(f"Error registering user: {e}")
            return AuthResponse(
                success=False,
                message=f"Registration failed: {str(e)}"
            )
    
    async def login_user(self, login_data: UserLogin) -> AuthResponse:
        """Authenticate user and return JWT token"""
        try:
            # Get user by email
            user = await self.get_user_by_email(login_data.email)
            if not user:
                return AuthResponse(
                    success=False,
                    message="Invalid email or password"
                )
            
            # Get user with password hash
            result = self.supabase.table("users").select("*").eq("email", login_data.email).execute()
            if not result.data:
                return AuthResponse(
                    success=False,
                    message="Invalid email or password"
                )
            
            user_data = result.data[0]
            password_hash = user_data.get("password_hash")
            
            if not password_hash:
                return AuthResponse(
                    success=False,
                    message="Invalid email or password"
                )
            
            # Verify password
            if not self.verify_password(login_data.password, password_hash):
                return AuthResponse(
                    success=False,
                    message="Invalid email or password"
                )
            
            # Create access token
            access_token_expires = timedelta(minutes=self.access_token_expire_minutes)
            access_token = self.create_access_token(
                data={"user_id": user.id, "email": user.email, "first_name": user.first_name},
                expires_delta=access_token_expires
            )
            
            token = Token(
                access_token=access_token,
                token_type="bearer",
                expires_in=self.access_token_expire_minutes * 60,
                user_id=user.id,
                email=user.email,
                first_name=user.first_name
            )
            
            return AuthResponse(
                success=True,
                message="Login successful",
                token=token
            )
            
        except Exception as e:
            logger.error(f"Error logging in user: {e}")
            return AuthResponse(
                success=False,
                message=f"Login failed: {str(e)}"
            )
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = self.supabase.table("users").select("*").eq("email", email).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
    
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            raise
    
    async def change_password(self, user_id: int, current_password: str, new_password: str) -> AuthResponse:
        """Change user password"""
        try:
            # Get user with password hash
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            if not result.data:
                return AuthResponse(
                    success=False,
                    message="User not found"
                )
            
            user_data = result.data[0]
            password_hash = user_data.get("password_hash")
            
            if not password_hash:
                return AuthResponse(
                    success=False,
                    message="Password not set for this user"
                )
            
            # Verify current password
            if not self.verify_password(current_password, password_hash):
                return AuthResponse(
                    success=False,
                    message="Current password is incorrect"
                )
            
            # Hash new password
            new_password_hash = self.get_password_hash(new_password)
            
            # Update password in database
            self.supabase.table("users").update({"password_hash": new_password_hash}).eq("id", user_id).execute()
            
            return AuthResponse(
                success=True,
                message="Password changed successfully"
            )
            
        except Exception as e:
            logger.error(f"Error changing password: {e}")
            return AuthResponse(
                success=False,
                message=f"Password change failed: {str(e)}"
            ) 