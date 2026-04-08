from typing import Dict, Any
import json

from app.AI.session_store import (
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

def handle_message(user_id: int, message: Any) -> Dict[str, Any]:

    session = get_session(user_id)
    state = session.get("state", "idle")

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
            return {
                "message": "Please select a doctor and time slot properly.",
                "current_state": "awaiting_slot_selection",
                "ui": {"component": "none"},
                "actions": []
            }

        result = book_appointment(
            patient_id=user_id,
            doctor_id=doctor_id,
            hospital_id = session.get("hospital_id") or 1,
            department_id=session.get("department_id") or 1,
            slot_time=slot
        )

        if result["status"] == "success":
            clear_session(user_id)

            return {
                "message": f"Appointment confirmed at {result.get('scheduled_at')}",
                "current_state": "completed",
                "ui": {"component": "none"},
                "actions": []
            }

        return {
            "message": f"Booking failed: {result['message']}",
            "current_state": "awaiting_slot_selection",
            "ui": {"component": "none"},
            "actions": []
        }

    # ===============================
    # STEP 2: CALL LLM
    # ===============================

    ai_response = call_llm(
        user_id=user_id,
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
            return {
                "message": "No doctors available right now.",
                "current_state": "idle",
                "ui": {"component": "none"},
                "actions": []
            }

        update_session(user_id, {
            "state": "awaiting_slot_selection",
            "hospital_id": hospital_id,
            "department_id": department_id
        })

        return {
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
        }

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
                return {
                    "message": "No available doctors or slots.",
                    "current_state": "idle",
                    "ui": {"component": "none"},
                    "actions": []
                }

            update_session(user_id, {
                "state": "awaiting_slot_selection",
                "hospital_id": hospital_id,
                "department_id": department_id
            })

            return {
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
            }

    # ===============================
    # STEP 5: UPDATE STATE
    # ===============================

    update_session(user_id, {
        "state": ai_response.get("current_state", state)
    })

    return ai_response


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