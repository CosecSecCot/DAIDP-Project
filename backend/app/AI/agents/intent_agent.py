# ai/agents/intent_agent.py

"""
Production-grade intent detection agent.

Features:
- 20+ hospital front desk intents
- Strong structured prompt
- Robust JSON parsing
- Entity normalization
- Safe fallback handling
"""

from typing import Tuple, Dict, Any
from app.AI.services.openai_service import call_llm_json


# ===============================
# INTENT LIST (FULL SYSTEM)
# ===============================

SUPPORTED_INTENTS = [
    "book_appointment",
    "cancel_appointment",
    "reschedule_appointment",
    "check_availability",
    "triage",
    "doctor_info",
    "hospital_info",
    "billing_inquiry",
    "lab_results",
    "prescription_request",
    "medical_records",
    "emergency",
    "greeting",
    "goodbye",
    "thanks",
    "complaint",
    "feedback",
    "update_profile",
    "insurance_query",
    "unknown"
]


# ===============================
# SYSTEM PROMPT (VERY IMPORTANT)
# ===============================

SYSTEM_PROMPT = """
You are an AI front desk assistant for a hospital.

Your task:
- Identify user intent
- Extract structured entities

STRICT RULES:
- Output ONLY valid JSON
- No explanation
- No extra text

SUPPORTED INTENTS:
book_appointment
cancel_appointment
reschedule_appointment
check_availability
triage
doctor_info
hospital_info
billing_inquiry
lab_results
prescription_request
medical_records
emergency
greeting
goodbye
thanks
complaint
feedback
update_profile
insurance_query
unknown

ENTITY RULES:
- date → "YYYY-MM-DD" if possible
- time_preference → "morning" | "afternoon" | "evening"
- symptoms → list of strings
- doctor_speciality → cardiology, dermatology, general, etc
- appointment_id → number if mentioned

EXAMPLES:

User: "I have fever and headache"
Output:
{
  "intent": "triage",
  "entities": {
    "symptoms": ["fever", "headache"]
  }
}

User: "Book appointment tomorrow morning"
Output:
{
  "intent": "book_appointment",
  "entities": {
    "date": "2026-04-05",
    "time_preference": "morning"
  }
}

User: "Cancel my appointment 123"
Output:
{
  "intent": "cancel_appointment",
  "entities": {
    "appointment_id": 123
  }
}

User: "Hi"
Output:
{
  "intent": "greeting",
  "entities": {}
}
"""


# ===============================
# MAIN FUNCTION
# ===============================

def get_intent(message: str) -> Tuple[str, Dict[str, Any]]:
    """
    Detect intent + entities using LLM.

    Returns:
        (intent, entities)
    """

    try:
        result = call_llm_json(SYSTEM_PROMPT, message)

        intent = result.get("intent", "unknown")
        entities = result.get("entities", {})

        # validate intent
        if intent not in SUPPORTED_INTENTS:
            intent = "unknown"

        # normalize entities
        entities = _normalize_entities(entities)

        return intent, entities

    except Exception as e:
        print(f"[IntentAgent] Error: {e}")
        return "unknown", {}


# ===============================
# ENTITY NORMALIZATION
# ===============================

def _normalize_entities(entities: Dict[str, Any]) -> Dict[str, Any]:
    """
    Clean and standardize entity values
    """

    normalized = {}

    for key, value in entities.items():

        if value is None:
            continue

        # normalize strings
        if isinstance(value, str):
            normalized[key] = value.strip().lower()

        # normalize list
        elif isinstance(value, list):
            normalized[key] = [str(v).strip().lower() for v in value]

        # keep numbers as-is
        else:
            normalized[key] = value

    return normalized