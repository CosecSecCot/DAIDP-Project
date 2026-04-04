# ai/orchestrator.py

"""
Production-grade AI orchestrator.

Responsibilities:
- Manage conversation state
- Route to agents
- Handle workflows
- Return user-friendly responses
"""

from typing import Dict, Any

from app.AI.session_store import (
    get_session,
    update_session,
    clear_session
)

from app.AI.agents.intent_agent import get_intent
from app.AI.agents.scheduling_agent import get_available_slots
from app.AI.agents.booking_agent import book_appointment


# ===============================
# MAIN ENTRY
# ===============================

def handle_message(user_id: int, message: str) -> Dict[str, str]:
    """
    Main AI entry point
    """

    session = get_session(user_id)

    # ===============================
    # STEP 1: HANDLE ACTIVE FLOWS
    # ===============================

    if session.get("flow") == "booking":

        # expecting slot selection
        if session.get("awaiting_slot"):

            slot = message.strip()

            result = book_appointment(
                patient_id=user_id,
                doctor_id=session["doctor_id"],
                hospital_id=session["hospital_id"],
                department_id=session["department_id"],
                slot_time=slot
            )

            clear_session(user_id)

            if result["status"] == "success":
                return {
                    "response": f"✅ Appointment confirmed at {slot}"
                }
            else:
                return {
                    "response": f"❌ {result['message']}"
                }

    # ===============================
    # STEP 2: INTENT DETECTION
    # ===============================

    intent, entities = get_intent(message)

    print(f"[DEBUG] Intent: {intent}, Entities: {entities}")

    # ===============================
    # STEP 3: ROUTING LOGIC
    # ===============================

    # 🔥 BOOK APPOINTMENT
    if intent == "book_appointment":

        hospital_id = 1  # from auth/session (future)
        department_id = 1  # improve later

        slots_data = get_available_slots(
            patient_id=user_id,
            hospital_id=hospital_id,
            entities=entities
        )

        if not slots_data["slots"]:
            return {
                "response": "❌ No available slots. Try another day."
            }

        # save session
        update_session(user_id, {
            "flow": "booking",
            "awaiting_slot": True,
            "doctor_id": slots_data["doctor_id"],
            "hospital_id": hospital_id,
            "department_id": department_id,
            "entities": entities
        })

        return {
            "response": (
                f"Available slots: {slots_data['slots']}\n"
                f"👉 Recommended: {slots_data['recommended']}\n"
                f"Please choose a time."
            )
        }

    # 🔥 CHECK AVAILABILITY
    if intent == "check_availability":

        slots_data = get_available_slots(
            patient_id=user_id,
            hospital_id=1,
            entities=entities
        )

        return {
            "response": f"Available slots: {slots_data['slots']}"
        }

    # 🔥 CANCEL APPOINTMENT
    if intent == "cancel_appointment":
        return {
            "response": "Please provide appointment ID to cancel."
        }

    # 🔥 RESCHEDULE
    if intent == "reschedule_appointment":
        return {
            "response": "Please provide appointment ID and new date."
        }

    # 🔥 TRIAGE
    if intent == "triage":

        symptoms = entities.get("symptoms", [])

        if not symptoms:
            return {
                "response": "Please tell your symptoms."
            }

        return {
            "response": f"Based on symptoms {symptoms}, you should consult a doctor."
        }

    # 🔥 BILLING
    if intent == "billing_inquiry":
        return {
            "response": "Your billing details are available in your account."
        }

    # 🔥 LAB
    if intent == "lab_results":
        return {
            "response": "Lab results will be shared soon."
        }

    # 🔥 PRESCRIPTION
    if intent == "prescription_request":
        return {
            "response": "Prescription request submitted."
        }

    # 🔥 DOCTOR INFO
    if intent == "doctor_info":
        return {
            "response": "We have specialists in cardiology, dermatology, and general medicine."
        }

    # 🔥 HOSPITAL INFO
    if intent == "hospital_info":
        return {
            "response": "Hospital is open 9AM to 8PM."
        }

    # 🔥 GREETING
    if intent == "greeting":
        return {
            "response": "Hello! How can I assist you today?"
        }

    # 🔥 THANKS
    if intent == "thanks":
        return {
            "response": "You're welcome 😊"
        }

    # 🔥 GOODBYE
    if intent == "goodbye":
        return {
            "response": "Take care! 👋"
        }

    # 🔥 COMPLAINT
    if intent == "complaint":
        return {
            "response": "We’re sorry. Our team will contact you."
        }

    # 🔥 FEEDBACK
    if intent == "feedback":
        return {
            "response": "Thank you for your feedback!"
        }

    # 🔥 DEFAULT
    return {
        "response": "🤖 I didn’t understand. You can say 'book appointment'."
    }