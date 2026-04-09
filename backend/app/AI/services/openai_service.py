"""
OpenAI service layer for AI front desk.

Responsibilities:
- Call OpenAI API
- Enforce structured JSON output
- Inject system prompt
- Pass conversation context
- Handle errors safely
"""

import json
from typing import Dict, Any, List

from openai import OpenAI

from app.AI.session_store import get_history

# ===============================
# INIT CLIENT
# ===============================

client = OpenAI()


# ===============================
# SYSTEM PROMPT
# ===============================

SYSTEM_PROMPT = """
You are a professional hospital front desk assistant.

Your behavior:
- Talk like a human receptionist
- Be polite, helpful, and clear
- Do NOT jump directly to booking
- Ask follow-up questions step by step
- Understand patient symptoms before suggesting a doctor
1. When asking questions, use MCQ format.
2. Do NOT ask open-ended questions when options can be provided.
3. Use "mcq" component when appropriate
4. Use "none" ONLY when:
   - giving information
   - confirming booking
- Once enough information is gathered, recommend any doctor from list of doctors
- Then trigger actions like fetching slots
- Guide user until appointment is booked

STRICT RESPONSE FORMAT (JSON ONLY):

{
  "message": "string",
  "current_state": "string",
  "ui": {
    "component": "mcq | none | timeslot_picker | confirmation",
    "data": {}
  },
  "actions": []
}

EXAMPLES:

If asking duration:
{
  "message": "How long have you had fever?",
  "current_state": "collecting_symptoms",
  "ui": {
    "component": "mcq",
    "data": {
      "question": "Duration of fever?",
      "options": [
        "Less than 1 day",
        "1-3 days",
        "More than 3 days"
      ]
    }
  },
  "actions": []
}

If asking symptoms:
{
  "message": "Do you have any of these symptoms?",
  "current_state": "collecting_symptoms",
  "ui": {
    "component": "mcq",
    "data": {
      "question": "Select symptoms",
      "options": [
        "Cough",
        "Body pain",
        "Headache",
        "None"
      ]
    }
  },
  "actions": []
}

IMPORTANT:
- Prefer MCQ over text
- Be structured
RULES:
- Always return valid JSON
- Never return plain text
- Use "actions" only when backend work is needed
- Use "ui.component" values:
  - "none"
  - "mcq"
  - "timeslot_picker"
  - "confirmation"

STATE GUIDE:
- idle
- collecting_symptoms
- suggest_doctor
- awaiting_slot_selection
- completed
"""


# ===============================
# MAIN FUNCTION
# ===============================

def generate_ai_response(
    user_id: int,
    chat_id: int,
    message: Any,
    state: str
) -> Dict[str, Any]:
    """
    Main OpenAI call
    """

    try:
        # ===============================
        # GET HISTORY
        # ===============================

        history = get_history(user_id, chat_id=chat_id, limit=10)

        messages: List[Dict[str, str]] = [
            {
                "role": "system",
                "content": SYSTEM_PROMPT + f"\n\nCurrent state: {state}"
            }
        ]

        # add history
        for h in history:
            content = _history_to_prompt_content(h)
            messages.append({
                "role": h["role"],
                "content": content
            })

        # add current message
        messages.append({
            "role": "user",
            "content": _payload_to_prompt_content(message)
        })

        # ===============================
        # OPENAI CALL
        # ===============================

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.3
        )

        content = response.choices[0].message.content

        # ===============================
        # PARSE JSON
        # ===============================

        data = json.loads(content)

        # ===============================
        # VALIDATION (VERY IMPORTANT)
        # ===============================

        if "message" not in data:
            raise ValueError("Missing message field")

        if "current_state" not in data:
            data["current_state"] = state

        if "ui" not in data:
            data["ui"] = {"component": "none"}

        if "actions" not in data:
            data["actions"] = []

        return data

    except Exception as e:
        print("[OPENAI ERROR]", str(e))

        # fallback response
        return {
            "message": "Sorry, I am having trouble understanding. Please try again.",
            "current_state": state,
            "ui": {"component": "none"},
            "actions": []
        }


def _history_to_prompt_content(entry: Dict[str, Any]) -> str:
    content = entry.get("content")

    if isinstance(content, dict):
        if entry.get("role") == "assistant" and isinstance(content.get("message"), str):
            return content["message"]
        return json.dumps(content)

    if isinstance(content, list):
        return json.dumps(content)

    return str(content)


def _payload_to_prompt_content(payload: Any) -> str:
    if isinstance(payload, dict):
        return json.dumps(payload)

    if isinstance(payload, list):
        return json.dumps(payload)

    return str(payload)
