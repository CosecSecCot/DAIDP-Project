# routers/ai.py

"""
AI Router (Production Ready)

Responsibilities:
- Expose AI endpoint
- Validate request
- Call orchestrator
- Handle errors safely
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
import logging

from app.AI.orchestrator import handle_message


# ===============================
# LOGGER
# ===============================

logger = logging.getLogger("ai.router")
logger.setLevel(logging.INFO)


# ===============================
# REQUEST / RESPONSE MODELS
# ===============================

class ChatRequest(BaseModel):
    user_id: int = Field(..., example=1)
    message: str = Field(..., example="I want to book appointment")

class ChatResponse(BaseModel):
    response: str


# ===============================
# ROUTER
# ===============================

router = APIRouter(prefix="/ai", tags=["AI"])


@router.post("/chat", response_model=ChatResponse)
def chat(request: ChatRequest):
    """
    Main AI endpoint

    Example:
    POST /ai/chat
    {
        "user_id": 1,
        "message": "Book appointment tomorrow"
    }
    """

    try:
        logger.info(f"[AI] User {request.user_id}: {request.message}")

        result = handle_message(
            user_id=request.user_id,
            message=request.message
        )

        return ChatResponse(response=result["response"])

    except ValueError as ve:
        logger.warning(f"[AI] Validation error: {str(ve)}")

        raise HTTPException(
            status_code=400,
            detail=str(ve)
        )

    except Exception as e:
        logger.error(f"[AI] Internal error: {str(e)}")

        raise HTTPException(
            status_code=500,
            detail="Internal server error"
        )