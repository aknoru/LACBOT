"""
Authentication API routes
"""

from fastapi import APIRouter, HTTPException, Depends, status
from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import timedelta
import re

from app.core.security import (
    verify_password, 
    get_password_hash, 
    create_access_token,
    get_current_user
)
from app.core.database import get_supabase_client
from app.core.config import settings

router = APIRouter()

# Request/Response models
class UserRegister(BaseModel):
    email: EmailStr
    username: str
    full_name: str
    password: str
    language_preference: Optional[str] = "en"

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class Token(BaseModel):
    access_token: str
    token_type: str
    user_id: str
    role: str

class UserProfile(BaseModel):
    id: str
    email: str
    username: str
    full_name: str
    role: str
    language_preference: str
    created_at: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

def validate_password(password: str) -> bool:
    """Validate password strength"""
    if len(password) < 8:
        return False
    if not re.search(r"[A-Z]", password):
        return False
    if not re.search(r"[a-z]", password):
        return False
    if not re.search(r"\d", password):
        return False
    return True

@router.post("/register", response_model=Token)
async def register(user_data: UserRegister):
    """
    Register a new user
    """
    try:
        supabase = get_supabase_client()
        
        # Validate password
        if not validate_password(user_data.password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
            )
        
        # Check if user already exists
        existing_user = supabase.table("users").select("*").eq(
            "email", user_data.email
        ).execute()
        
        if existing_user.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check username availability
        existing_username = supabase.table("users").select("*").eq(
            "username", user_data.username
        ).execute()
        
        if existing_username.data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
        
        # Validate language preference
        if user_data.language_preference not in settings.SUPPORTED_LANGUAGES:
            user_data.language_preference = "en"
        
        # Create user
        user_data_dict = {
            "email": user_data.email,
            "username": user_data.username,
            "full_name": user_data.full_name,
            "password_hash": get_password_hash(user_data.password),
            "language_preference": user_data.language_preference,
            "role": "user",
            "is_active": True
        }
        
        result = supabase.table("users").insert(user_data_dict).execute()
        user = result.data[0]
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"]}, expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user["id"],
            role=user["role"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=Token)
async def login(user_data: UserLogin):
    """
    Login user and return access token
    """
    try:
        supabase = get_supabase_client()
        
        # Get user by email
        user = supabase.table("users").select("*").eq(
            "email", user_data.email
        ).execute()
        
        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        user = user.data[0]
        
        # Verify password
        if not verify_password(user_data.password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if user is active
        if not user.get("is_active", True):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is deactivated"
            )
        
        # Create access token
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = create_access_token(
            data={"sub": user["id"]}, expires_delta=access_token_expires
        )
        
        return Token(
            access_token=access_token,
            token_type="bearer",
            user_id=user["id"],
            role=user["role"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.get("/profile", response_model=UserProfile)
async def get_profile(current_user: dict = Depends(get_current_user)):
    """
    Get current user profile
    """
    try:
        return UserProfile(
            id=current_user["id"],
            email=current_user["email"],
            username=current_user["username"],
            full_name=current_user["full_name"],
            role=current_user["role"],
            language_preference=current_user["language_preference"],
            created_at=current_user["created_at"]
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get profile: {str(e)}"
        )

@router.put("/profile")
async def update_profile(
    profile_data: dict,
    current_user: dict = Depends(get_current_user)
):
    """
    Update user profile
    """
    try:
        supabase = get_supabase_client()
        
        # Validate language preference
        if "language_preference" in profile_data:
            if profile_data["language_preference"] not in settings.SUPPORTED_LANGUAGES:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid language preference"
                )
        
        # Update user
        result = supabase.table("users").update(profile_data).eq(
            "id", current_user["id"]
        ).execute()
        
        return {"message": "Profile updated successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update profile: {str(e)}"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: dict = Depends(get_current_user)
):
    """
    Change user password
    """
    try:
        supabase = get_supabase_client()
        
        # Get current user
        user = supabase.table("users").select("*").eq(
            "id", current_user["id"]
        ).execute()
        
        if not user.data:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user = user.data[0]
        
        # Verify current password
        if not verify_password(password_data.current_password, user["password_hash"]):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Validate new password
        if not validate_password(password_data.new_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="New password must be at least 8 characters long and contain uppercase, lowercase, and numbers"
            )
        
        # Update password
        new_password_hash = get_password_hash(password_data.new_password)
        supabase.table("users").update({
            "password_hash": new_password_hash
        }).eq("id", current_user["id"]).execute()
        
        return {"message": "Password changed successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to change password: {str(e)}"
        )

@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout user (client-side token removal)
    """
    # In a stateless JWT system, logout is handled client-side
    # by removing the token from storage
    return {"message": "Logged out successfully"}

@router.get("/verify-token")
async def verify_token(current_user: dict = Depends(get_current_user)):
    """
    Verify if the current token is valid
    """
    return {
        "valid": True,
        "user_id": current_user["id"],
        "role": current_user["role"]
    }

