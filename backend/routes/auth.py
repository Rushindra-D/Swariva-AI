"""
SWARIVA AI — Authentication Endpoints
Supabase user registration, sign-in, session verification, and profile management.
"""
from typing import Dict, Any
from fastapi import APIRouter, HTTPException, status, Depends

from schemas.auth import (
    SignUpRequest,
    SignInRequest,
    AuthResponse,
    UserProfileResponse,
)
from repositories.auth_repo import AuthRepository
from auth import require_current_user

router = APIRouter(prefix="/api/v1/auth", tags=["Authentication & Profiles"])


@router.post("/signup", response_model=AuthResponse, summary="Register a new user")
async def register_user(req: SignUpRequest):
    """
    Registers a new user account in Supabase Auth.
    Automatically triggers user profile creation.
    """
    try:
        user_data = await AuthRepository.sign_up(
            email=req.email,
            password=req.password,
            full_name=req.full_name or "Swariva User",
            preferred_language=req.preferred_language or "auto",
        )
        return AuthResponse(**user_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration error: {str(e)}",
        )


@router.post("/login", response_model=AuthResponse, summary="Sign in user")
async def login_user(req: SignInRequest):
    """
    Authenticates user credentials against Supabase Auth.
    Returns access_token (JWT) to authorize subsequent requests.
    """
    try:
        auth_data = await AuthRepository.sign_in(
            email=req.email,
            password=req.password,
        )
        return AuthResponse(**auth_data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login error: {str(e)}",
        )


@router.get("/me", response_model=UserProfileResponse, summary="Get current user profile")
async def get_my_profile(current_user: Dict[str, Any] = Depends(require_current_user)):
    """
    Fetches the profile for the currently authenticated user.
    """
    user_id = current_user["id"]
    profile = await AuthRepository.get_profile(user_id)
    if not profile:
        profile = {
            "id": user_id,
            "email": current_user.get("email"),
            "full_name": current_user.get("user_metadata", {}).get("full_name", "Swariva User"),
            "preferred_language": "auto",
        }
    return UserProfileResponse(**profile)


@router.post("/logout", summary="Sign out user")
async def logout_user():
    """
    Terminates the user's active session.
    """
    return {"success": True, "message": "Signed out successfully."}

