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


router = APIRouter(
    prefix="/ai",
    tags=["AI"]
)


# ===============================
# REQUEST SCHEMA (FIXED)
# ===============================

class ChatRequest(BaseModel):
    user_id: int = Field(..., description="User ID")

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
    message: str
    current_state: str
    ui: UIComponent
    actions: list


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
            message=request.message
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