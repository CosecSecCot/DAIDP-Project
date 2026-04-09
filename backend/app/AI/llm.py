"""
LLM wrapper layer.

Responsibilities:
- Provide clean interface to orchestrator
- Call OpenAI service
- Enrich context (state, history, memory)
- Normalize AI output
- Add safety + fallback handling
"""

from typing import Dict, Any

from app.AI.services.openai_service import generate_ai_response


# ===============================
# MAIN ENTRY
# ===============================

def call_llm(
    user_id: int,
    chat_id: int,
    message: Any,
    state: str
) -> Dict[str, Any]:
    """
    Main function used by orchestrator.

    Flow:
    1. Call OpenAI
    2. Normalize output
    3. Return structured JSON
    """

    # ===============================
    # STEP 1: CALL OPENAI
    # ===============================

    ai_response = generate_ai_response(
        user_id=user_id,
        chat_id=chat_id,
        message=message,
        state=state
    )

    # ===============================
    # STEP 3: VALIDATE RESPONSE
    # ===============================

    ai_response = _normalize_response(ai_response, state)

    return ai_response


# ===============================
# NORMALIZATION
# ===============================

def _normalize_response(
    data: Dict[str, Any],
    state: str
) -> Dict[str, Any]:
    """
    Ensure response is always valid
    """

    # message
    if "message" not in data or not isinstance(data["message"], str):
        data["message"] = "Sorry, something went wrong."

    # state
    if "current_state" not in data or not isinstance(data["current_state"], str):
        data["current_state"] = state

    # ui
    if "ui" not in data or not isinstance(data["ui"], dict):
        data["ui"] = {"component": "none"}

    if "component" not in data["ui"]:
        data["ui"]["component"] = "none"

    # actions
    if "actions" not in data or not isinstance(data["actions"], list):
        data["actions"] = []

    return data


# ===============================
# OPTIONAL: SMART HELPERS
# ===============================

def is_action_required(ai_response: Dict[str, Any]) -> bool:
    """
    Check if backend needs to execute something
    """
    return len(ai_response.get("actions", [])) > 0


def get_first_action(ai_response: Dict[str, Any]) -> Dict[str, Any]:
    """
    Get first action safely
    """
    actions = ai_response.get("actions", [])
    if not actions:
        return {}
    return actions[0]
