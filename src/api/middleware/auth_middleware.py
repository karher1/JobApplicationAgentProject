from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from typing import Optional

from src.services.auth_service import AuthService
from src.models.auth import TokenData

# Initialize security scheme
security = HTTPBearer()

# Initialize auth service
auth_service = AuthService()

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> TokenData:
    """Get current authenticated user from JWT token"""
    try:
        # Initialize auth service if not already done
        if not auth_service.supabase:
            await auth_service.initialize()
        
        token = credentials.credentials
        token_data = auth_service.verify_token(token)
        
        if token_data is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Could not validate credentials",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        return token_data
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

async def get_current_user_id(current_user: TokenData = Depends(get_current_user)) -> int:
    """Get current user ID from authenticated token"""
    return current_user.user_id

async def get_current_user_email(current_user: TokenData = Depends(get_current_user)) -> str:
    """Get current user email from authenticated token"""
    return current_user.email

# Optional authentication - doesn't raise error if no token
async def get_optional_current_user(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[TokenData]:
    """Get current user if authenticated, otherwise return None"""
    if credentials is None:
        return None
    
    try:
        # Initialize auth service if not already done
        if not auth_service.supabase:
            await auth_service.initialize()
        
        token = credentials.credentials
        token_data = auth_service.verify_token(token)
        
        return token_data
    except Exception:
        return None 