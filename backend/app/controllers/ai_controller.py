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
    AlertData,
    AlertUI,
    PatientContext,
    RespondToUserArgs,
)

from openai import OpenAI


MAX_TOOL_ROUNDS = 6
HISTORY_LIMIT = 10


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
    db_patient_context = load_patient_and_profile
    from app.config.database import SessionLocal

    db = SessionLocal()
    try:
        patient, health_profile = db_patient_context(user_id, db)
        if patient is None:
            return PatientContext(patient_id=user_id)

        payload = normalize_patient_context(patient)
        payload["health_profile"] = health_profile
        return PatientContext.model_validate(payload)
    finally:
        db.close()


def _build_messages(
    patient_context: PatientContext,
    history: List[Dict[str, Any]],
    incoming_message: Any,
) -> List[Dict[str, str]]:
    messages: List[Dict[str, str]] = [
        {
            "role": "system",
            "content": (
                build_system_prompt()
                + "\n\nConversation context:\n"
                + json.dumps(patient_context.model_dump(mode="json"), default=str)
                + "\n\nThe user is not affiliated with any hospital. Do not assume otherwise."
            ),
        }
    ]

    for item in history:
        role = item.get("role", "user")
        content = _message_to_llm_content(item)
        messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": _stringify_message(incoming_message)})
    return messages


def _execute_action(tool_name: str, arguments: Dict[str, Any]) -> Dict[str, Any]:
    spec = ACTION_REGISTRY.get(tool_name)
    if spec is None:
        raise ValueError(f"Unknown tool: {tool_name}")

    typed_input = spec.input_model.model_validate(arguments)
    output = spec.executor(typed_input)
    if isinstance(output, str):
        return {"summary": output}
    if hasattr(output, "model_dump"):
        return output.model_dump(mode="json")
    if isinstance(output, dict):
        return output
    return {"summary": str(output)}


def _action_record_from_output(
    tool_name: str, input_data: Dict[str, Any], output: Dict[str, Any]
) -> ActionRecord:
    summary = str(output.get("summary") or output.get("message") or "Completed.")
    status = ActionStatus.SUCCESS
    if summary.lower().startswith(("failed", "error", "not found", "unable")):
        status = ActionStatus.FAILED
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
    payload = RespondToUserArgs.model_validate(arguments).model_dump(mode="json")
    response = AgentResponse.model_validate(payload)
    if not response.actions:
        response.actions = executed_actions
    return response


def handle_chat_message(
    user_id: int,
    message: Any,
    chat_id: Optional[int] = None,
) -> ChatResponse:
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
    messages = _build_messages(patient_context, history, message)
    tools = build_openai_tools()
    executed_actions: List[ActionRecord] = []

    final_response: Optional[AgentResponse] = None

    for _ in range(MAX_TOOL_ROUNDS):
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            tools=tools,
            tool_choice="required",
            temperature=0.2,
        )

        assistant_message = completion.choices[0].message
        tool_calls = assistant_message.tool_calls or []

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
        final_response = AgentResponse(
            message="I am sorry, I could not complete that request right now.",
            ui=AlertUI(
                component="alert",
                data=AlertData(
                    title="Request could not be completed",
                    message="Please try again in a moment.",
                    level="error",
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

    return ChatResponse(
        chat_id=chat_id,
        message=final_response.message,
        ui=final_response.ui,
        actions=final_response.actions,
    )
