"""
SWARIVA AI — FastAPI Authentication Dependencies
Extracts and validates Supabase JWT Bearer tokens from incoming HTTP headers.
"""
from typing import Optional, Dict, Any
from fastapi import Header, HTTPException, status, Depends

from repositories.auth_repo import AuthRepository


async def get_current_user(
    authorization: Optional[str] = Header(None, description="Bearer <Supabase-JWT-Token>")
) -> Optional[Dict[str, Any]]:
    """
    Extracts and verifies the user token if provided.
    Returns user dict with 'id', 'email', etc., or None for guest requests.
    """
    if not authorization:
        return None

    user = await AuthRepository.verify_token(authorization)
    return user


async def require_current_user(
    user: Optional[Dict[str, Any]] = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Strict dependency that enforces authentication.
    Raises HTTP 401 Unauthorized if token is missing or invalid.
    """
    if not user or not user.get("id"):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please sign in.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user

