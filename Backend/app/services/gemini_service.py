from google import genai
from google.genai import types
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.config import settings
from app.models.session import ChatSession
from app.models.message import Message
from app.services.redis_service import (
    get_history,
    set_history,
    is_available as redis_available
)

client = genai.Client(api_key=settings.GOOGLE_API_KEY)
MODEL = "gemini-3.1-flash-lite"

PERSONAS = {
    "default": """You are a helpful AI assistant. 
Answer clearly and concisely.""",

    "support": """You are a friendly customer support agent.
Your goal is to help users solve their problems.
Be empathetic, patient, and solution-focused.
If you cannot solve something, escalate politely.
Always end with: 'Is there anything else I can help you with?'""",

    "code_reviewer": """You are an expert code reviewer.
Review code for bugs, performance issues, and best practices.
Be specific about line numbers and provide improved versions.
Use markdown code blocks in your responses.
Focus on: correctness, efficiency, readability, security.""",

    "document_analyst": """You are a document analysis expert.
Help users understand, summarize, and extract insights from documents.
Be precise with citations and page references.
Highlight key findings and actionable insights.
Structure your responses with clear headings."""
}

def get_system_prompt(persona: str = "default") -> str:
    return PERSONAS.get(persona, PERSONAS["default"])

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

def _build_contents(
    history: list,
    user_message: str,
    persona: str = "default"
) -> list:
    contents = []

    # Add system prompt as first user message
    # Gemini doesn't have a system role — we prepend it
    system_prompt = get_system_prompt(persona)
    if system_prompt and not history:
        contents.append(
            types.Content(
                role="user",
                parts=[types.Part(
                    text=f"[System]: {system_prompt}"
                )]
            )
        )
        contents.append(
            types.Content(
                role="model",
                parts=[types.Part(
                    text="Understood. I'll follow those instructions."
                )]
            )
        )

    for msg in history:
        contents.append(
            types.Content(
                role=msg["role"],
                parts=[types.Part(text=msg["parts"][0])]
            )
        )

    contents.append(
        types.Content(
            role="user",
            parts=[types.Part(text=user_message)]
        )
    )
    return contents

async def _load_history(
    db: AsyncSession,
    session_id: str
) -> list:
    """
    Load conversation history.
    Tries Redis first, falls back to PostgreSQL.
    """
    if redis_available():
        cached = get_history(session_id)
        if cached:
            print(f"✅ Cache HIT — {len(cached)} messages from Redis")
            return cached
        print("Cache MISS — loading from PostgreSQL")

    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at)
    )
    messages = result.scalars().all()

    history = [
        {
            "role": "user" if msg.role == "user" else "model",
            "parts": [msg.content]
        }
        for msg in messages[-20:]
    ]

    if redis_available() and history:
        set_history(session_id, history)
        print(f"✅ Cached {len(history)} messages in Redis")

    return history

async def _save_messages(
    db: AsyncSession,
    session_id: str,
    user_message: str,
    ai_reply: str,
    history: list,
    is_first_message: bool = False
):
    """Save messages to PostgreSQL and update Redis cache"""
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

    # Update Redis cache
    if redis_available():
        history.append({"role": "user", "parts": [user_message]})
        history.append({"role": "model", "parts": [ai_reply]})
        set_history(session_id, history)
        print("✅ Redis cache updated")

async def get_ai_response(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    user_message: str
) -> str:
    """Non-streaming response"""
    await get_or_create_session(db, user_id, session_id)
    history = await _load_history(db, session_id)
    is_first = len(history) == 0

    contents = _build_contents(history, user_message)

    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=contents
        )
        ai_reply = response.text
    except Exception as e:
        raise Exception(f"Gemini error: {str(e)}")

    await _save_messages(
        db, session_id,
        user_message, ai_reply,
        history, is_first
    )

    return ai_reply

async def get_ai_response_stream(
    db: AsyncSession,
    user_id: str,
    session_id: str,
    user_message: str,
    persona: str = "default"   # ← add this
):
    await get_or_create_session(db, user_id, session_id)
    history = await _load_history(db, session_id)
    is_first = len(history) == 0

    contents = _build_contents(history, user_message, persona)  # ← pass persona

    full_reply = ""
    try:
        for chunk in client.models.generate_content_stream(
            model=MODEL,
            contents=contents
        ):
            if chunk.text:
                full_reply += chunk.text
                yield chunk.text
    except Exception as e:
        yield f"Error: {str(e)}"
        return

    await _save_messages(
        db, session_id,
        user_message, full_reply,
        history, is_first
    )

async def generate_session_title(first_message: str) -> str:
    """Auto-generate a short session title from first message"""
    try:
        response = client.models.generate_content(
            model=MODEL,
            contents=[types.Content(
                role="user",
                parts=[types.Part(
                    text=f"Generate a very short title (max 4 words) "
                         f"for a chat starting with: '{first_message}'. "
                         f"Return only the title, nothing else."
                )]
            )]
        )
        return response.text.strip()[:50]
    except Exception:
        return first_message[:30]

async def get_session_history(
    db: AsyncSession,
    session_id: str
) -> list:
    """Get full message history for a session from PostgreSQL"""
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