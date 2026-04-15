from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from app.controllers.ai_history import (
    append_chat_message,
    ensure_chat_session,
    get_persisted_history,
)
from app.controllers.agent_actions.common import (
    load_patient_and_profile,
    normalize_patient_context,
)
from app.controllers.agent_actions.registry import (
    ACTION_REGISTRY,
    build_openai_tools,
    build_system_prompt,
)
from app.models.ai import (
    ActionRecord,
    ActionStatus,
    AgentResponse,
    ChatResponse,
    AlertLevel,
    AlertData,
    AlertUI,
    NoneUI,
    PatientContext,
    RespondToUserArgs,
)

from openai import OpenAI


MAX_TOOL_ROUNDS = 6
HISTORY_LIMIT = 10
WARMUP_USER_TURNS = 2


client = OpenAI()


def _stringify_message(message: Any) -> str:
    if isinstance(message, str):
        return message
    return json.dumps(message, default=str)


def _message_to_llm_content(message: Dict[str, Any]) -> str:
    content = message.get("content")
    if isinstance(content, dict):
        return json.dumps(content, default=str)
    if isinstance(content, list):
        return json.dumps(content, default=str)
    if content is None:
        return ""
    return str(content)


def _load_patient_context(user_id: int) -> PatientContext:
    print("\n=== DEBUG: Loading patient context ===")
    db_patient_context = load_patient_and_profile
    from app.config.database import SessionLocal

    db = SessionLocal()
    try:
        patient, health_profile = db_patient_context(user_id, db)
        print("Patient:", patient)
        print("Health profile:", health_profile)

        if patient is None:
            print("No patient found, returning minimal context")
            return PatientContext(patient_id=user_id)

        payload = normalize_patient_context(patient)
        payload["health_profile"] = health_profile

        print("Normalized payload:", json.dumps(payload, default=str, indent=2))

        return PatientContext.model_validate(payload)
    finally:
        db.close()


def _build_messages(
    patient_context: PatientContext,
    history: List[Dict[str, Any]],
    incoming_message: Any,
    *,
    warmup_mode: bool,
) -> List[Dict[str, str]]:
    print("\n=== DEBUG: Building messages ===")
    print("Warmup mode:", warmup_mode)
    print("Incoming message:", incoming_message)

    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                build_system_prompt(warmup_mode=warmup_mode)
                + "\n\nConversation context:\n"
                + json.dumps(patient_context.model_dump(mode="json"), default=str)
                + "\n\nThe user is not affiliated with any hospital. Do not assume otherwise."
                + (
                    "\n\nWarm-up mode is only a hint: prefer gathering as much useful context as possible "
                    "which could be useful when viewed by a doctor before acting, unless user intent is explicit."
                    if warmup_mode
                    else ""
                )
            ),
        }
    ]

    print("\n=== DEBUG: History ===")
    print(json.dumps(history, indent=2, default=str))

    for item in history:
        role = item.get("role", "user")
        content = _message_to_llm_content(item)
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": _stringify_message(incoming_message)})

    print("\n=== DEBUG: Final Messages Sent to LLM ===")
    print(json.dumps(messages, indent=2, default=str))

    return messages


def _count_user_turns(history: List[Dict[str, Any]]) -> int:
    return sum(1 for item in history if item.get("role") == "user")


def _is_warmup_phase(history: List[Dict[str, Any]]) -> bool:
    turns = _count_user_turns(history)
    print("\n=== DEBUG: User turns ===", turns)
    return turns < WARMUP_USER_TURNS


def _execute_action(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    print("\n=== DEBUG: Executing action ===")
    print("Tool:", tool_name)
    print("Arguments:", json.dumps(arguments, indent=2))

    spec = ACTION_REGISTRY.get(tool_name)
    if spec is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    typed_input = spec.input_model.model_validate(arguments)
    print("Typed input:", typed_input)

    output = spec.executor(typed_input)
    print("Raw output:", output)

    if isinstance(output, str):
        result = {"summary": output}
    elif hasattr(output, "model_dump"):
        result = output.model_dump(mode="json")
    elif isinstance(output, dict):
        result = output
    else:
        result = {"summary": str(output)}

    print("Final action output:", json.dumps(result, indent=2, default=str))
    return result


def _action_record_from_output(
    tool_name: str, input_data: Dict[str, Any], output: Dict[str, Any]
) -> ActionRecord:
    print("\n=== DEBUG: Creating action record ===")
    print("Tool:", tool_name)
    print("Output:", json.dumps(output, indent=2, default=str))

    summary = str(output.get("summary") or output.get("message") or "Completed.")
    status = ActionStatus.SUCCESS
    if any(word in summary.lower() for word in ["failed", "error", "not found", "unable"]):
        status = ActionStatus.FAILED

    print("Summary:", summary)
    print("Status:", status)

    return ActionRecord(
        name=tool_name,
        status=status,
        summary=summary,
        input=input_data,
        output=output,
    )


def _response_from_tool_arguments(
    arguments: Dict[str, Any], executed_actions: List[ActionRecord]
) -> AgentResponse:
    print("\n=== DEBUG: respond_to_user called ===")
    print("Arguments received:")
    print(json.dumps(arguments, indent=2, default=str))

    try:
        payload = RespondToUserArgs.model_validate(arguments).model_dump(mode="json")
        print("Validation success")
    except Exception as e:
        import traceback
        print("\n=== VALIDATION ERROR ===")
        print("Error:", repr(e))
        print("Arguments were:")
        print(json.dumps(arguments, indent=2, default=str))
        traceback.print_exc()
        raise

    response = AgentResponse.model_validate(payload)

    if not response.actions:
        response.actions = executed_actions

    print("\n=== FINAL RESPONSE OBJECT ===")
    print(response.model_dump(mode="json"))

    return response


def handle_chat_message(
    user_id: int,
    message: Any,
    chat_id: Optional[int] = None,
) -> ChatResponse:
    print("\n================ NEW CHAT REQUEST ================")
    print("User ID:", user_id)
    print("Message:", message)

    session = ensure_chat_session(
        user_id=user_id,
        chat_id=chat_id,
        initial_message=message,
    )
    chat_id = session["id"]

    append_chat_message(
        user_id=user_id,
        chat_id=chat_id,
        role="user",
        content=message,
        status="completed",
    )

    patient_context = _load_patient_context(user_id)
    history = get_persisted_history(
        user_id=user_id, chat_id=chat_id, limit=HISTORY_LIMIT
    )

    warmup_mode = _is_warmup_phase(history)

    messages = _build_messages(
        patient_context,
        history,
        message,
        warmup_mode=warmup_mode,
    )

    tools = build_openai_tools()
    print("\n=== DEBUG: Tools available ===")
    print([t["function"]["name"] for t in tools])

    executed_actions: List[ActionRecord] = []

    final_response: Optional[AgentResponse] = None

    for i in range(MAX_TOOL_ROUNDS):
        print(f"\n=== TOOL LOOP ITERATION {i} ===")

        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="required",
            temperature=0.2,
        )

        assistant_message = completion.choices[0].message
        tool_calls = assistant_message.tool_calls or []

        print("\n=== DEBUG: Assistant message ===")
        print("Content:", assistant_message.content)
        print("Tool calls:", tool_calls)

        if not tool_calls:
            raise RuntimeError("Model returned no tool call.")

        messages.append(
            {
                "role": "assistant",
                "content": assistant_message.content or "",
                "tool_calls": [
                    {
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    }
                    for tool_call in tool_calls
                ],
            }
        )

        for tool_call in tool_calls:
            tool_name = tool_call.function.name
            raw_arguments = json.loads(tool_call.function.arguments or "{}")

            print("\n=== DEBUG: Tool Call ===")
            print("Tool:", tool_name)
            print("Args:", json.dumps(raw_arguments, indent=2))

            if tool_name == "respond_to_user":
                final_response = _response_from_tool_arguments(
                    raw_arguments, executed_actions
                )
                break

            action_output = _execute_action(tool_name, raw_arguments)

            executed_actions.append(
                _action_record_from_output(tool_name, raw_arguments, action_output)
            )

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(action_output, default=str),
                }
            )

        if final_response is not None:
            break

    if final_response is None:
        print("\n=== DEBUG: Fallback response triggered ===")

        final_response = AgentResponse(
            message="I am sorry, I could not complete that request right now.",
            ui=AlertUI(
                component="alert",
                data=AlertData(
                    title="Request could not be completed",
                    message="Please try again in a moment.",
                    level=AlertLevel.ERROR,
                ),
            ),
            actions=executed_actions,
        )

    append_chat_message(
        user_id=user_id,
        chat_id=chat_id,
        role="assistant",
        content=final_response.model_dump(mode="json"),
        status="completed",
        extra={
            "tool_count": len(executed_actions),
            "response_type": "final",
        },
    )

    print("\n=== FINAL RESPONSE SENT TO USER ===")
    print(final_response.model_dump(mode="json"))

    return ChatResponse(
        chat_id=chat_id,
        message=final_response.message,
        ui=final_response.ui,
        actions=final_response.actions,
    )