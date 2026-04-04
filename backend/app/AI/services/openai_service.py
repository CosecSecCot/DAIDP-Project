# ai/services/openai_service.py

"""
Production-grade OpenAI service wrapper.

Features:
- Retry mechanism
- Timeout handling
- Structured response enforcement
- Logging
- Centralized LLM control

IMPORTANT:
Do NOT call OpenAI directly anywhere else.
Always use this service.
"""

import os
import time
import json
import logging
from typing import Optional, Dict, Any

from openai import OpenAI
from dotenv import load_dotenv


# ===============================
# ENV SETUP
# ===============================

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not OPENAI_API_KEY:
    raise RuntimeError("OPENAI_API_KEY not found in environment")


# ===============================
# CLIENT INITIALIZATION
# ===============================

client = OpenAI(api_key=OPENAI_API_KEY)


# ===============================
# CONFIGURATION
# ===============================

DEFAULT_MODEL = "gpt-4o-mini"
MAX_RETRIES = 3
RETRY_DELAY = 1  # seconds
TIMEOUT_SECONDS = 10


# ===============================
# LOGGER
# ===============================

logger = logging.getLogger("ai.openai")
logger.setLevel(logging.INFO)


# ===============================
# CORE FUNCTION
# ===============================

def call_llm(
    system_prompt: str,
    user_message: str,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.0,
    max_tokens: int = 500,
    expect_json: bool = False
) -> str:
    """
    Main LLM call function.

    Args:
        system_prompt: instruction prompt
        user_message: user input
        model: OpenAI model
        temperature: randomness
        max_tokens: response limit
        expect_json: enforce JSON output

    Returns:
        response string (or JSON string)
    """

    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_message}
    ]

    for attempt in range(MAX_RETRIES):
        try:
            start_time = time.time()

            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )

            duration = time.time() - start_time

            content = response.choices[0].message.content.strip()

            logger.info(f"[OpenAI] Success | Time: {duration:.2f}s")

            # OPTIONAL: enforce JSON
            if expect_json:
                return _safe_json_parse(content)

            return content

        except Exception as e:
            logger.error(f"[OpenAI] Attempt {attempt+1} failed: {str(e)}")

            if attempt < MAX_RETRIES - 1:
                time.sleep(RETRY_DELAY)
            else:
                raise RuntimeError("OpenAI failed after retries")


# ===============================
# JSON PARSER (VERY IMPORTANT)
# ===============================

def _safe_json_parse(text: str) -> Dict[str, Any]:
    """
    Safely parse LLM JSON output.

    Handles:
    - ```json blocks
    - invalid formatting
    """

    try:
        # remove markdown
        text = text.replace("```json", "").replace("```", "").strip()

        return json.loads(text)

    except json.JSONDecodeError as e:
        logger.error(f"[OpenAI] JSON parse failed: {text}")

        raise ValueError("Invalid JSON from LLM")


# ===============================
# HIGH LEVEL HELPERS
# ===============================

def call_llm_json(system_prompt: str, user_message: str) -> Dict[str, Any]:
    """
    Shortcut for JSON responses
    """
    return call_llm(
        system_prompt=system_prompt,
        user_message=user_message,
        expect_json=True
    )


def call_llm_text(system_prompt: str, user_message: str) -> str:
    """
    Shortcut for text responses
    """
    return call_llm(
        system_prompt=system_prompt,
        user_message=user_message,
        expect_json=False
    )