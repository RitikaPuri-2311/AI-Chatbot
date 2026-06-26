import google.generativeai as genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.config import settings
from app.models.session import ChatSession
from app.models.message import Message

genai.configure(api_key=settings.GOOGLE_API_KEY)
model = genai.GenerativeModel("gemini-2.5-flash")

async def get_or_create_session(
    db: AsyncSession,
    user_id: str,
    session_id: str
) -> ChatSession:
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id,
            ChatSession.user_id == user_id
        )
    )
    session = result.scalar_one_or_none()
    if not session:
        try:
            session = ChatSession(
                id=session_id,
                user_id=user_id,
                title="New Chat"
            )
            db.add(session)
            await db.commit()
            await db.refresh(session)
        except Exception:
            await db.rollback()
            result = await db.execute(
                select(ChatSession).where(
                    ChatSession.id == session_id,
                    ChatSession.user_id == user_id
                )
            )
            session = result.scalar_one_or_none()
    return session

async def get_ai_response(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    user_message: str
) -> str:
    await get_or_create_session(db, user_id, session_id)

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    history = []
    for msg in messages[-20:]:
        history.append({
            "role": "user" if msg.role == "user" else "model",
            "parts": [msg.content]
        })

    chat = model.start_chat(history=history)
    response = chat.send_message(user_message)
    ai_reply = response.text

    try:
        db.add(Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_message
        ))
        db.add(Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=ai_reply
        ))
        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error saving messages: {e}")

    return ai_reply

async def get_ai_response_stream(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    user_message: str
):
    await get_or_create_session(db, user_id, session_id)

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    is_first_message = len(messages) == 0

    history = []
    for msg in messages[-20:]:
        history.append({
            "role": "user" if msg.role == "user" else "model",
            "parts": [msg.content]
        })

    chat = model.start_chat(history=history)
    response = chat.send_message(user_message, stream=True)

    full_reply = ""
    for chunk in response:
        if chunk.text:
            full_reply += chunk.text
            yield chunk.text

    try:
        db.add(Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="user",
            content=user_message
        ))
        db.add(Message(
            id=str(uuid.uuid4()),
            session_id=session_id,
            role="assistant",
            content=full_reply
        ))

        # Auto title on first message
        if is_first_message:
            title = await generate_session_title(user_message)
            await db.execute(
                ChatSession.__table__.update()
                .where(ChatSession.id == session_id)
                .values(title=title)
            )

        await db.commit()
    except Exception as e:
        await db.rollback()
        print(f"Error saving messages: {e}")

async def get_session_history(
    db: AsyncSession,
    session_id: str
) -> list:
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()
    return [
        {
            "id": msg.id,
            "role": msg.role,
            "content": msg.content,
            "createdAt": msg.created_at.isoformat()
            if msg.created_at else ""
        }
        for msg in messages
    ]
async def generate_session_title(first_message: str) -> str:
    try:
        response = model.generate_content(
            f"Generate a very short title (max 4 words) for a "
            f"chat that starts with: '{first_message}'. "
            f"Return only the title, nothing else."
        )
        return response.text.strip()[:50]
    except Exception:
        return first_message[:30]