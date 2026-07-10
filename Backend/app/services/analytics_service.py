"""Analytics queries for support conversations."""

from __future__ import annotations

from collections import Counter

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.conversation import Conversation
from app.models.message import ConversationMessage
from app.utils.sentiment import classify_sentiment


def format_duration(seconds: float) -> str:
    if seconds <= 0:
        return "0s"
    minutes = int(seconds // 60)
    secs = int(seconds % 60)
    if minutes > 0:
        return f"{minutes}m {secs}s"
    return f"{secs}s"


async def get_conversation_overview(db: AsyncSession) -> dict:
    total_result = await db.execute(select(func.count(Conversation.id)))
    total_conversations = total_result.scalar() or 0

    persona_result = await db.execute(
        select(Conversation.persona, func.count(Conversation.id))
        .group_by(Conversation.persona)
        .order_by(func.count(Conversation.id).desc())
    )
    persona_rows = persona_result.all()
    most_used_persona = persona_rows[0][0] if persona_rows else "support"

    msg_count_result = await db.execute(
        select(
            ConversationMessage.conversation_id,
            func.count(ConversationMessage.id),
        ).group_by(ConversationMessage.conversation_id)
    )
    message_counts = [row[1] for row in msg_count_result.all()]
    average_messages = (
        sum(message_counts) / len(message_counts) if message_counts else 0.0
    )

    duration_result = await db.execute(
        select(
            ConversationMessage.conversation_id,
            func.min(ConversationMessage.created_at),
            func.max(ConversationMessage.created_at),
        ).group_by(ConversationMessage.conversation_id)
    )
    durations: list[float] = []
    for _, first_at, last_at in duration_result.all():
        if first_at and last_at and last_at > first_at:
            durations.append((last_at - first_at).total_seconds())

    average_duration = format_duration(
        sum(durations) / len(durations) if durations else 0.0
    )

    return {
        "total_conversations": total_conversations,
        "average_duration": average_duration,
        "average_messages": round(average_messages, 1),
        "most_used_persona": most_used_persona,
    }


async def get_topic_analytics(db: AsyncSession) -> dict:
    result = await db.execute(
        select(ConversationMessage.intent, func.count(ConversationMessage.id))
        .where(
            ConversationMessage.intent.is_not(None),
            ConversationMessage.role == "user",
        )
        .group_by(ConversationMessage.intent)
        .order_by(func.count(ConversationMessage.id).desc())
    )

    topics = [
        {"topic": intent or "Unknown", "count": count}
        for intent, count in result.all()
    ]
    return {"topics": topics}


async def get_sentiment_analytics(db: AsyncSession) -> dict:
    result = await db.execute(
        select(ConversationMessage.content).where(
            ConversationMessage.role == "user"
        )
    )
    counts = Counter({"positive": 0, "neutral": 0, "negative": 0})
    for (content,) in result.all():
        counts[classify_sentiment(content)] += 1

    return {
        "positive": counts["positive"],
        "neutral": counts["neutral"],
        "negative": counts["negative"],
    }
