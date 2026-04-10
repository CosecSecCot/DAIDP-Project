from __future__ import annotations

from fastapi import APIRouter, HTTPException

from app.controllers.ai_controller import handle_chat_message
from app.controllers.ai_history import ensure_chat_session, get_persisted_history, list_chat_sessions
from app.models.ai import ChatHistoryMessage, ChatRequest, ChatResponse, ChatSessionResponse


router = APIRouter(prefix="/ai-v2", tags=["AI V2"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return handle_chat_message(
            user_id=request.user_id,
            message=request.message,
            chat_id=request.chat_id,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"AI processing failed: {exc}") from exc


@router.post("/chats", response_model=ChatSessionResponse)
def create_chat_session(request: ChatRequest) -> ChatSessionResponse:
    session = ensure_chat_session(
        user_id=request.user_id,
        chat_id=request.chat_id,
        initial_message=request.message,
    )
    return ChatSessionResponse.model_validate(session)


@router.get("/chats/{user_id}", response_model=list[ChatSessionResponse])
def get_user_chat_sessions(user_id: int) -> list[ChatSessionResponse]:
    return [ChatSessionResponse.model_validate(item) for item in list_chat_sessions(user_id)]


@router.get("/history/{user_id}", response_model=list[ChatHistoryMessage])
def get_chat_history(user_id: int, chat_id: int | None = None, limit: int | None = None) -> list[ChatHistoryMessage]:
    return [ChatHistoryMessage.model_validate(item) for item in get_persisted_history(user_id=user_id, chat_id=chat_id, limit=limit)]

