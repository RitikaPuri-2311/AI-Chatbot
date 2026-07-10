from pydantic import BaseModel, Field


class TopicCount(BaseModel):
    topic: str
    count: int


class TopicAnalyticsResponse(BaseModel):
    topics: list[TopicCount]


class ConversationOverviewResponse(BaseModel):
    total_conversations: int
    average_duration: str
    average_messages: float
    most_used_persona: str


class SentimentAnalyticsResponse(BaseModel):
    positive: int
    neutral: int
    negative: int
