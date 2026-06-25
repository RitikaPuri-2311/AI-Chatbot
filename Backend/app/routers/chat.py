from fastapi import APIRouter, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from app.services.gemini_service import (
    get_ai_response, get_session_history
)
from app.services.auth_service import decode_token, get_user_by_email

router = APIRouter(prefix="/chat", tags=["chat"])
security = HTTPBearer()

class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"

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

@router.post("/")
def chat(
    body: ChatRequest,
    current_user: dict = Depends(get_current_user)
):
    try:
        # Use user_id + session_id as unique key
        session_key = f"{current_user['id']}_{body.session_id}"
        ai_reply = get_ai_response(session_key, body.message)
        
        return {
            "id": "msg_" + str(hash(ai_reply))[-6:],
            "role": "assistant",
            "content": ai_reply,
            "session_id": body.session_id
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, 
            detail=f"AI error: {str(e)}"
        )

@router.get("/history/{session_id}")
def get_history(
    session_id: str,
    current_user: dict = Depends(get_current_user)
):
    session_key = f"{current_user['id']}_{session_id}"
    messages = get_session_history(session_key)
    return {"messages": messages}