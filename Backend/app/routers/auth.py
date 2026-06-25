from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.services.auth_service import (
    register_user, login_user, 
    create_access_token, decode_token,
    get_user_by_email
)

router = APIRouter(prefix="/auth", tags=["auth"])
security = HTTPBearer()

class RegisterRequest(BaseModel):
    email: str
    username: str
    password: str

class LoginRequest(BaseModel):
    email: str
    password: str

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
):
    token = credentials.credentials
    payload = decode_token(token)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid token")
    
    email = payload.get("sub")
    user = get_user_by_email(email)
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

@router.post("/register")
def register(body: RegisterRequest):
    try:
        user = register_user(body.email, body.username, body.password)
        token = create_access_token({"sub": user["email"]})
        return {
            "accessToken": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"]
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/login")
def login(body: LoginRequest):
    try:
        user = login_user(body.email, body.password)
        token = create_access_token({"sub": user["email"]})
        return {
            "accessToken": token,
            "user": {
                "id": user["id"],
                "email": user["email"],
                "username": user["username"]
            }
        }
    except ValueError as e:
        raise HTTPException(status_code=401, detail=str(e))

@router.get("/me")
def me(current_user: dict = Depends(get_current_user)):
    return {
        "id": current_user["id"],
        "email": current_user["email"],
        "username": current_user["username"]
    }