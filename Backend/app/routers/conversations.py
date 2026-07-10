from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.dependencies import require_permission
from app.schemas.conversation import (
    AddMessageRequest,
    AddMessageResponse,
    ConversationHistoryResponse,
    ConversationResponse,
    CreateConversationRequest,
    MessageResponse,
)
from app.services import conversation_service

router = APIRouter(prefix="/conversations", tags=["conversations"])


@router.post(
    "",
    response_model=ConversationResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_conversation(
    body: CreateConversationRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("ai:chat")),
):
    conversation = await conversation_service.create_conversation(
        db=db,
        user_id=current_user.id,
        title=body.title,
        persona=body.persona,
    )
    return ConversationResponse(
        id=conversation.id,
        title=conversation.title,
        persona=conversation.persona,
        created_at=conversation.created_at,
    )


@router.post(
    "/{conversation_id}/messages",
    response_model=AddMessageResponse,
)
async def add_message(
    conversation_id: str,
    body: AddMessageRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("ai:chat")),
):
    if body.role != "user":
        from fastapi import HTTPException
        raise HTTPException(
            status_code=400,
            detail="Only user messages can be submitted to this endpoint",
        )

    result = await conversation_service.add_message_and_respond(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
        content=body.content.strip(),
    )
    return AddMessageResponse(
        conversation_id=result["conversation_id"],
        message=MessageResponse(**result["message"]),
    )


@router.get(
    "/{conversation_id}",
    response_model=ConversationHistoryResponse,
)
async def get_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("ai:chat")),
):
    data = await conversation_service.get_conversation_history(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return ConversationHistoryResponse(**data)


@router.delete(
    "/{conversation_id}",
    status_code=status.HTTP_200_OK,
)
async def delete_conversation(
    conversation_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(require_permission("ai:chat")),
):
    await conversation_service.delete_conversation(
        db=db,
        conversation_id=conversation_id,
        user_id=current_user.id,
    )
    return {"message": "Conversation deleted"}
