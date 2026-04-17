from __future__ import annotations

import logging
from io import BytesIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from gtts import gTTS
from sqlalchemy.orm import Session

from app.config.database import get_db
from app.controllers.ai_controller import handle_chat_message
from app.controllers.ai_history import ensure_chat_session, get_persisted_history, list_chat_sessions
from app.models.ai_chat import AIChatMessage
from app.models.ai import ChatHistoryMessage, ChatRequest, ChatResponse, ChatSessionResponse


router = APIRouter(prefix="/ai-v2", tags=["AI V2"])
logger = logging.getLogger(__name__)


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    try:
        return handle_chat_message(
            user_id=request.user_id,
            message=request.message,
            chat_id=request.chat_id,
        )
    except Exception as exc:
        print("CHAT ERROR: ", exc)
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


@router.get("/audio/{chat_id}")
def get_latest_assistant_audio(chat_id: int, db: Session = Depends(get_db)) -> StreamingResponse:
    message = (
        db.query(AIChatMessage)
        .filter(
            AIChatMessage.chat_session_id == chat_id,
            AIChatMessage.role == "assistant",
        )
        .order_by(AIChatMessage.timestamp.desc(), AIChatMessage.id.desc())
        .first()
    )

    if message is None:
        raise HTTPException(status_code=404, detail="No assistant message found for this chat.")

    if message.role != "assistant":
        raise HTTPException(status_code=404, detail="No assistant message found for this chat.")

    content = message.content if isinstance(message.content, dict) else None
    text = content.get("message") if content else None
    if not isinstance(text, str) or not text.strip():
        raise HTTPException(status_code=400, detail="Assistant message text is empty or invalid.")

    audio_buffer = BytesIO()
    try:
        gTTS(text=text.strip(), lang="en").write_to_fp(audio_buffer)
    except Exception as exc:
        logger.exception("Failed to generate TTS audio for chat_id=%s message_id=%s", chat_id, message.id)
        raise HTTPException(status_code=500, detail="Failed to generate audio.") from exc

    audio_buffer.seek(0)
    return StreamingResponse(
        audio_buffer,
        media_type="audio/mpeg",
        headers={"Content-Disposition": f'inline; filename="chat-{chat_id}-latest-assistant.mp3"'},
    )