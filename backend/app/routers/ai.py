"""
AI Router

Responsibilities:
- Expose AI chat endpoint
- Accept both text + structured payload
- Call orchestrator
- Return structured response
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Union, Dict, Any

from app.AI.orchestrator import handle_message
from app.AI.session_store import (
    ensure_chat_session,
    get_persisted_history,
    list_chat_sessions,
)


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# ===============================
# REQUEST SCHEMA (FIXED)
# ===============================

class ChatRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    chat_id: Optional[int] = Field(
        default=None,
        description="Existing chat session ID. Omit to create a new chat."
    )

    # ✅ FIX: allow both string and dict
    message: Union[str, Dict[str, Any]] = Field(
        ...,
        description="User message OR structured action payload"
    )


# ===============================
# RESPONSE SCHEMA
# ===============================

class UIComponent(BaseModel):
    component: str
    data: Optional[Dict[str, Any]] = None


class ChatResponse(BaseModel):
    chat_id: int
    message: str
    current_state: str
    status: str
    ui: UIComponent
    actions: list


class ChatSessionCreateRequest(BaseModel):
    user_id: int = Field(..., description="User ID")
    title: Optional[str] = Field(default=None, description="Optional chat title")


class ChatSessionResponse(BaseModel):
    id: int
    user_id: int
    title: str
    created_at: str
    updated_at: str


class ChatHistoryMessage(BaseModel):
    id: int
    chat_id: Optional[int] = None
    user_id: int
    role: str
    content: Any
    extra: Optional[Dict[str, Any]] = None
    status: str
    timestamp: str
    updated_at: Optional[str] = None


# ===============================
# MAIN ENDPOINT
# ===============================

@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main AI chat endpoint
    """

    try:
        response = handle_message(
            user_id=request.user_id,
            message=request.message,
            chat_id=request.chat_id
        )

        # safety validation
        if not isinstance(response, dict):
            raise ValueError("Invalid AI response type")

        if "message" not in response:
            raise ValueError("Missing message field")

        # ensure ui exists
        if "ui" not in response:
            response["ui"] = {"component": "none"}

        if "actions" not in response:
            response["actions"] = []

        return response

    except Exception as e:
        print("[AI ROUTER ERROR]", str(e))

        raise HTTPException(
            status_code=500,
            detail="AI processing failed"
        )


@router.post("/chats", response_model=ChatSessionResponse)
def create_chat_session(request: ChatSessionCreateRequest):
    try:
        session = ensure_chat_session(
            user_id=request.user_id,
            initial_message=request.title or "New chat",
            title=request.title
        )
        return session
    except Exception as e:
        print("[AI CHAT SESSION ERROR]", str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to create chat session"
        )


@router.get("/chats/{user_id}", response_model=list[ChatSessionResponse])
def get_user_chat_sessions(user_id: int):
    try:
        return list_chat_sessions(user_id=user_id)
    except Exception as e:
        print("[AI CHAT LIST ERROR]", str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch chat sessions"
        )


@router.get("/history/{user_id}", response_model=list[ChatHistoryMessage])
def get_chat_history(user_id: int, chat_id: Optional[int] = None, limit: Optional[int] = None):
    try:
        return get_persisted_history(user_id=user_id, chat_id=chat_id, limit=limit)
    except Exception as e:
        print("[AI HISTORY ERROR]", str(e))
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch chat history"
        )
