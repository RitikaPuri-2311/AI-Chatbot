from fastapi import Depends, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from app.database import get_db
from app.services.auth_service import decode_token, get_user_by_email

security = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
):
    """Get current user from JWT token — 401 if token missing/invalid"""
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(
            status_code=401,
            detail="Invalid or expired token"
        )
    email = payload.get("sub")
    user = await get_user_by_email(db, email)
    if not user:
        raise HTTPException(
            status_code=401,
            detail="User not found"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=401,
            detail="User account is disabled"
        )
    return user

def require_permission(permission: str):
    """
    Returns a dependency that checks if user has a specific permission.
    Raises 403 if permission is missing.
    
    Usage:
        @router.post("/")
        async def endpoint(
            user = Depends(require_permission("ai:chat"))
        ):
    """
    async def permission_checker(
        current_user=Depends(get_current_user)
    ):
        user_permissions = current_user.permissions or []
        if permission not in user_permissions:
            raise HTTPException(
                status_code=403,
                detail=f"Missing required permission: {permission}"
            )
        return current_user
    return permission_checker