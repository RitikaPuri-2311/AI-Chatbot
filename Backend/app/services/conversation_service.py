"""Business logic for support conversation management."""

from __future__ import annotations

import time
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.conversation import Conversation
from app.models.message import ConversationMessage
from app.services.support_tools import classify_intent


SUPPORT_PERSONAS = frozenset({"support", "default"})


def _format_timestamp(dt: datetime | None) -> datetime:
    return dt or datetime.now(timezone.utc)


def resolve_turn_intent(user_content: str, agent_result: dict | None = None) -> str:
    """Derive intent from agent output or keyword classifier (no LLM)."""
    if agent_result:
        query_mode = agent_result.get("query_mode")
        if query_mode == "company_faq":
            return "FAQ"

        tools = [call.get("tool") for call in agent_result.get("tool_calls", [])]
        if "check_order_status" in tools:
            return "Order Status"
        if "create_ticket" in tools:
            base = classify_intent(user_content)
            return base["intent"] if base["intent"] != "FAQ" else "Refund"
        if "escalate_to_human" in tools:
            return "Complaint"

    return classify_intent(user_content)["intent"]


def extract_tools_used(agent_result: dict | None) -> str | None:
    if not agent_result:
        return None
    names = [
        call.get("tool")
        for call in agent_result.get("tool_calls", [])
        if call.get("tool")
    ]
    return ", ".join(names) if names else None


async def invoke_support_agent(
    user_message: str,
    user_id: str,
    conversation_history: list[dict],
    session_id: str,
) -> dict:
    """Thin wrapper so tests can mock the agent without importing LangGraph."""
    from app.services.agent_service import run_document_agent

    return await run_document_agent(
        user_message=user_message,
        user_id=user_id,
        conversation_history=conversation_history,
        session_id=session_id,
    )


async def get_owned_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
) -> Conversation:
    result = await db.execute(
        select(Conversation)
        .options(selectinload(Conversation.messages))
        .where(
            Conversation.id == conversation_id,
            Conversation.user_id == user_id,
        )
    )
    conversation = result.scalar_one_or_none()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


async def create_conversation(
    db: AsyncSession,
    user_id: str,
    title: str,
    persona: str,
) -> Conversation:
    conversation = Conversation(
        id=str(uuid.uuid4()),
        user_id=user_id,
        title=title.strip(),
        persona=persona.strip(),
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)
    return conversation


def _build_agent_history(messages: list[ConversationMessage]) -> list[dict]:
    return [
        {"role": msg.role, "content": msg.content}
        for msg in messages
        if msg.role in ("user", "assistant")
    ]


async def add_message_and_respond(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
    content: str,
) -> dict:
    conversation = await get_owned_conversation(db, conversation_id, user_id)

    user_intent = classify_intent(content)["intent"]
    user_message = ConversationMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="user",
        content=content,
        intent=user_intent,
    )
    db.add(user_message)
    await db.flush()

    history = _build_agent_history(conversation.messages)
    start = time.perf_counter()
    agent_result: dict | None = None
    sources: list[dict] = []

    if conversation.persona in SUPPORT_PERSONAS:
        agent_result = await invoke_support_agent(
            user_message=content,
            user_id=user_id,
            conversation_history=history,
            session_id=conversation_id,
        )
        answer = agent_result.get("answer", "")
        sources = agent_result.get("sources") or []
    else:
        from app.services.gemini_service import generate_reply_with_persona

        answer = await generate_reply_with_persona(
            history=history,
            user_message=content,
            persona=conversation.persona,
        )

    elapsed_ms = int((time.perf_counter() - start) * 1000)
    turn_intent = resolve_turn_intent(content, agent_result)
    tools_used = extract_tools_used(agent_result)

    assistant_message = ConversationMessage(
        id=str(uuid.uuid4()),
        conversation_id=conversation_id,
        role="assistant",
        content=answer,
        intent=turn_intent,
        tool_used=tools_used,
        response_time_ms=elapsed_ms,
    )
    db.add(assistant_message)

    conversation.updated_at = datetime.now(timezone.utc)
    await db.commit()

    return {
        "conversation_id": conversation_id,
        "message": {
            "role": "assistant",
            "content": answer,
            "sources": sources,
        },
    }


async def get_conversation_history(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
) -> dict:
    conversation = await get_owned_conversation(db, conversation_id, user_id)
    return {
        "id": conversation.id,
        "persona": conversation.persona,
        "messages": [
            {
                "role": msg.role,
                "content": msg.content,
                "timestamp": _format_timestamp(msg.created_at),
            }
            for msg in conversation.messages
        ],
    }


async def delete_conversation(
    db: AsyncSession,
    conversation_id: str,
    user_id: str,
) -> None:
    conversation = await get_owned_conversation(db, conversation_id, user_id)
    await db.delete(conversation)
    await db.commit()
