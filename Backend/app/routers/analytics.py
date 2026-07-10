from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permission
from app.schemas.analytics import (
    ConversationOverviewResponse,
    SentimentAnalyticsResponse,
    TopicAnalyticsResponse,
)
from app.services import analytics_service

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get(
    "/conversations",
    response_model=ConversationOverviewResponse,
)
async def conversation_overview(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("ai:chat")),
):
    data = await analytics_service.get_conversation_overview(db)
    return ConversationOverviewResponse(**data)


@router.get(
    "/topics",
    response_model=TopicAnalyticsResponse,
)
async def topic_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("ai:chat")),
):
    data = await analytics_service.get_topic_analytics(db)
    return TopicAnalyticsResponse(**data)


@router.get(
    "/sentiment",
    response_model=SentimentAnalyticsResponse,
)
async def sentiment_analytics(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("ai:chat")),
):
    data = await analytics_service.get_sentiment_analytics(db)
    return SentimentAnalyticsResponse(**data)
