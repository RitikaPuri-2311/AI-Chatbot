from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from app.database import get_db
from app.dependencies import get_current_user
from app.services.auth_service import (
    register_user, login_user,
    create_access_token
)

router = APIRouter(prefix="/auth", tags=["auth"])

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

@router.post("/register")
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await register_user(
            db, body.email, body.username, body.password
        )
        token = create_access_token({"sub": user.email})
        return {
            "accessToken": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "permissions": user.permissions
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db)
):
    try:
        user = await login_user(db, body.email, body.password)
        token = create_access_token({"sub": user.email})
        return {
            "accessToken": token,
            "user": {
                "id": user.id,
                "email": user.email,
                "username": user.username,
                "permissions": user.permissions
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me")
async def me(current_user=Depends(get_current_user)):
    return {
        "id": current_user.id,
        "email": current_user.email,
        "username": current_user.username,
        "permissions": current_user.permissions
    }