from typing import Dict, Any
import json

from app.AI.session_store import (
    append_history,
    complete_active_history,
    ensure_chat_session,
    get_session,
    update_session,
    clear_session
)

from app.AI.llm import call_llm
from app.AI.agents.scheduling_agent import get_available_slots
from app.AI.agents.booking_agent import book_appointment


# ===============================
# MAIN ENTRY
# ===============================

def handle_message(user_id: int, message: Any, chat_id: int | None = None) -> Dict[str, Any]:
    chat_session = ensure_chat_session(
        user_id=user_id,
        chat_id=chat_id,
        initial_message=message
    )
    chat_id = chat_session["id"]

    session = get_session(user_id, chat_id=chat_id)
    state = session.get("state", "idle")

    append_history(
        user_id=user_id,
        chat_id=chat_id,
        role="user",
        content=message,
        extra={"state_before": state},
        status="completed"
    )

    # ===============================
    # STEP 1: HANDLE SLOT SELECTION
    # ===============================

    if state == "awaiting_slot_selection":

        doctor_id = None
        slot = None

        # Case 1: dict input
        if isinstance(message, dict):
            doctor_id = message.get("doctor_id")
            slot = message.get("slot")

        # Case 2: string JSON
        elif isinstance(message, str):
            try:
                parsed = json.loads(message)
                doctor_id = parsed.get("doctor_id")
                slot = parsed.get("slot")
            except:
                pass

        if not doctor_id or not slot:
            return _finalize_response(user_id, chat_id, message, {
                "message": "Please select a doctor and time slot properly.",
                "current_state": "awaiting_slot_selection",
                "ui": {"component": "none"},
                "actions": []
            })

        result = book_appointment(
            patient_id=user_id,
            doctor_id=doctor_id,
            hospital_id = session.get("hospital_id") or 1,
            department_id=session.get("department_id") or 1,
            slot_time=slot
        )

        if result["status"] == "success":
            clear_session(user_id, chat_id=chat_id)

            return _finalize_response(user_id, chat_id, message, {
                "message": f"Appointment confirmed at {result.get('time')}",
                "current_state": "completed",
                "ui": {"component": "none"},
                "actions": []
            })

        return _finalize_response(user_id, chat_id, message, {
            "message": f"Booking failed: {result['message']}",
            "current_state": "awaiting_slot_selection",
            "ui": {"component": "none"},
            "actions": []
        })

    # ===============================
    # STEP 2: CALL LLM
    # ===============================

    ai_response = call_llm(
        user_id=user_id,
        chat_id=chat_id,
        message=message,
        state=state
    )

    # ===============================
    # STEP 3: AUTO TRIGGER SLOTS (CRITICAL FIX)
    # ===============================

    if ai_response.get("current_state") == "suggest_doctor":

        payload = {
            "symptoms": [str(message).lower()]
        }

        hospital_id = session.get("hospital_id", 1)
        department_id = _infer_department(payload)

        slots_data = get_available_slots(
            patient_id=user_id,
            hospital_id=hospital_id,
            entities=payload
        )

        if not slots_data.get("doctors"):
            return _finalize_response(user_id, chat_id, message, {
                "message": "No doctors available right now.",
                "current_state": "idle",
                "ui": {"component": "none"},
                "actions": []
            })

        update_session(user_id, {
            "state": "awaiting_slot_selection",
            "hospital_id": hospital_id,
            "department_id": department_id
        }, chat_id=chat_id)

        return _finalize_response(user_id, chat_id, message, {
            "message": "Here are available doctors and slots:",
            "current_state": "awaiting_slot_selection",
            "ui": {
                "component": "doctor_slot_picker",
                "data": {
                    "doctors": slots_data["doctors"],
                    "recommended": slots_data.get("recommended")
                }
            },
            "actions": []
        })

    # ===============================
    # STEP 4: HANDLE ACTIONS
    # ===============================

    actions = ai_response.get("actions", [])

    for action in actions:

        if action["type"] == "get_slots":

            payload = action.get("payload", {})

            hospital_id = session.get("hospital_id", 1)
            department_id = _infer_department(payload)

            slots_data = get_available_slots(
                patient_id=user_id,
                hospital_id=hospital_id,
                entities=payload
            )

            if not slots_data.get("doctors"):
                return _finalize_response(user_id, chat_id, message, {
                    "message": "No available doctors or slots.",
                    "current_state": "idle",
                    "ui": {"component": "none"},
                    "actions": []
                })

            update_session(user_id, {
                "state": "awaiting_slot_selection",
                "hospital_id": hospital_id,
                "department_id": department_id
            }, chat_id=chat_id)

            return _finalize_response(user_id, chat_id, message, {
                "message": "Available doctors and slots:",
                "current_state": "awaiting_slot_selection",
                "ui": {
                    "component": "doctor_slot_picker",
                    "data": {
                        "doctors": slots_data["doctors"],
                        "recommended": slots_data.get("recommended")
                    }
                },
                "actions": []
            })

    # ===============================
    # STEP 5: UPDATE STATE
    # ===============================

    update_session(user_id, {
        "state": ai_response.get("current_state", state)
    }, chat_id=chat_id)

    return _finalize_response(user_id, chat_id, message, ai_response)


# ===============================
# HELPERS
# ===============================

def _infer_department(payload: Dict[str, Any]) -> int:

    speciality = payload.get("specialisation")

    if not speciality:
        text = str(payload).lower()

        if "heart" in text or "chest" in text:
            speciality = "cardiology"
        elif "skin" in text:
            speciality = "dermatology"
        else:
            speciality = "general"

    mapping = {
        "general": 1,
        "cardiology": 2,
        "dermatology": 3
    }

    return mapping.get(speciality, 1)


def _resolve_status(current_state: str) -> str:
    return "completed" if current_state in {"completed", "idle"} else "active"


def _finalize_response(
    user_id: int,
    chat_id: int,
    message: Any,
    response: Dict[str, Any]
) -> Dict[str, Any]:
    response["chat_id"] = chat_id
    response["status"] = _resolve_status(response.get("current_state", "idle"))

    complete_active_history(user_id, chat_id=chat_id, role="assistant")

    append_history(
        user_id=user_id,
        chat_id=chat_id,
        role="assistant",
        content=response,
        extra={
            "current_state": response.get("current_state"),
            "ui_component": response.get("ui", {}).get("component", "none")
        },
        status=response["status"]
    )

    update_session(user_id, {
        "last_message": message,
        "last_ai_message": response.get("message"),
        "state": response.get("current_state", "idle")
    }, chat_id=chat_id)

    return response
