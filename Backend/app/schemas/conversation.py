from datetime import datetime
from typing import Optional

from pydantic import BaseModel, Field


class CreateConversationRequest(BaseModel):
    title: str = Field(..., min_length=1, max_length=200)
    persona: str = Field(default="support", min_length=1, max_length=50)


class ConversationResponse(BaseModel):
    id: str
    title: str
    persona: str
    created_at: datetime


class AddMessageRequest(BaseModel):
    role: str = Field(..., pattern="^(user|assistant)$")
    content: str = Field(..., min_length=1)


class MessageResponse(BaseModel):
    role: str
    content: str
    sources: list[dict] = Field(default_factory=list)


class AddMessageResponse(BaseModel):
    conversation_id: str
    message: MessageResponse


class HistoryMessage(BaseModel):
    role: str
    content: str
    timestamp: datetime


class ConversationHistoryResponse(BaseModel):
    id: str
    persona: str
    messages: list[HistoryMessage]
