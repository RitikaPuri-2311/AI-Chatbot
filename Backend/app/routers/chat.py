from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from pydantic import BaseModel
import uuid
from app.database import get_db
from app.dependencies import require_permission, get_current_user
from app.services.gemini_service import (
    get_ai_response,
    get_ai_response_stream,
    get_session_history
)
from app.models.session import ChatSession as ChatSessionModel
from app.models.message import Message as MessageModel
from app.services.redis_service import delete_session as redis_delete

router = APIRouter(prefix="/chat", tags=["chat"])

class ChatRequest(BaseModel):
    message: str
    session_id: str = "session-001"
    persona: str = "default"

@router.post("/")
async def chat(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    # Requires ai:chat permission — 403 if missing
    current_user=Depends(require_permission("ai:chat"))
):
    try:
        ai_reply = await get_ai_response(
            db, current_user.id,
            body.session_id, body.message
        )
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

@router.post("/stream")
async def chat_stream(
    body: ChatRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("ai:chat"))
):
    async def generate():
        try:
            async for chunk in get_ai_response_stream(
                db,
                current_user.id,
                body.session_id,
                body.message,
                body.persona      # ← pass persona
            ):
                yield f"data: {chunk}\n\n"
        except Exception as e:
            yield f"data: [ERROR] {str(e)}\n\n"
        finally:
            yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no"
        }
    )

@router.get("/sessions")
async def get_sessions(
    db: AsyncSession = Depends(get_db),
    # Only needs auth — no specific permission
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(ChatSessionModel)
        .where(ChatSessionModel.user_id == current_user.id)
        .order_by(ChatSessionModel.created_at.desc())
    )
    sessions = result.scalars().all()
    return {
        "sessions": [
            {
                "id": s.id,
                "title": s.title,
                "createdAt": s.created_at.isoformat()
                if s.created_at else ""
            }
            for s in sessions
        ]
    }

@router.post("/sessions")
async def create_session(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    session = ChatSessionModel(
        id=str(uuid.uuid4()),
        user_id=current_user.id,
        title="New Chat"
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return {
        "id": session.id,
        "title": session.title,
        "createdAt": session.created_at.isoformat()
        if session.created_at else ""
    }

@router.patch("/sessions/{session_id}")
async def rename_session(
    session_id: str,
    body: dict,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    session.title = body.get("title", session.title)
    await db.commit()
    return {"id": session.id, "title": session.title}

@router.delete("/sessions/{session_id}")
async def delete_session(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    result = await db.execute(
        select(ChatSessionModel).where(
            ChatSessionModel.id == session_id,
            ChatSessionModel.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    await db.delete(session)
    await db.commit()

    # Clear Redis cache for this session
    redis_delete(session_id)

    return {"message": "Session deleted"}

@router.get("/history/{session_id}")
async def get_history(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    messages = await get_session_history(db, session_id)
    return {"messages": messages}

@router.get("/sessions/{session_id}/export")
async def export_conversation(
    session_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user)
):
    """Export conversation as plain text"""
    messages = await get_session_history(db, session_id)

    if not messages:
        raise HTTPException(404, "No messages found")

    lines = [f"AI Chatbot Conversation Export\n{'='*40}\n"]
    for msg in messages:
        role = "You" if msg["role"] == "user" else "AI"
        lines.append(f"{role}: {msg['content']}\n")

    text = "\n".join(lines)

    from fastapi.responses import PlainTextResponse
    return PlainTextResponse(
        content=text,
        headers={
            "Content-Disposition": f"attachment; filename=conversation-{session_id[:8]}.txt"
        }
    )