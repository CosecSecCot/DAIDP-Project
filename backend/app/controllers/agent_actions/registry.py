from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Type

from pydantic import BaseModel

from app.models.ai import (
    ActionRegistryEntry,
    AIUIComponent,
    AlertData,
    AlertUI,
    LookupSlotsInput,
    LookupSlotsOutput,
    BookAppointmentInput,
    BookAppointmentOutput,
    CancelAppointmentInput,
    CancelAppointmentOutput,
    GetUserInfoInput,
    GetUserInfoOutput,
    PickerData,
    PickerUI,
    RegistryBundle,
    RegistryExample,
    UIRegistryEntry,
    RespondToUserArgs,
)


@dataclass(slots=True)
class UIComponentSpec:
    name: str
    purpose: str
    when_to_use: str
    data_model: Type[BaseModel]
    examples: List[RegistryExample] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def component_schema(self) -> Dict[str, Any]:
        return self.data_model.model_json_schema()


@dataclass(slots=True)
class ActionSpec:
    name: str
    purpose: str
    when_to_use: str
    input_model: Type[BaseModel]
    output_model: Type[BaseModel]
    executor: Callable[[BaseModel], BaseModel]
    examples: List[RegistryExample] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    @property
    def input_schema(self) -> Dict[str, Any]:
        return self.input_model.model_json_schema()

    @property
    def output_schema(self) -> Dict[str, Any]:
        return self.output_model.model_json_schema()


UI_REGISTRY: Dict[str, UIComponentSpec] = {}
ACTION_REGISTRY: Dict[str, ActionSpec] = {}


def register_ui_component(spec: UIComponentSpec) -> None:
    UI_REGISTRY[spec.name] = spec


def register_action(spec: ActionSpec) -> None:
    ACTION_REGISTRY[spec.name] = spec


def build_registry_bundle() -> RegistryBundle:
    return RegistryBundle(
        ui_components=[
            UIRegistryEntry(
                name=spec.name,
                purpose=spec.purpose,
                when_to_use=spec.when_to_use,
                notes=spec.notes,
                examples=spec.examples,
                component_schema=spec.component_schema,
            )
            for spec in UI_REGISTRY.values()
        ],
        actions=[
            ActionRegistryEntry(
                name=spec.name,
                purpose=spec.purpose,
                when_to_use=spec.when_to_use,
                notes=spec.notes,
                examples=spec.examples,
                input_schema=spec.input_schema,
                output_schema=spec.output_schema,
            )
            for spec in ACTION_REGISTRY.values()
        ],
        rules=[
            "Use only the registered UI components and actions.",
            "If you need more information, ask for it with a picker or a short alert.",
            "When the response is ready, finish by calling respond_to_user.",
            "Do not invent new tools or output keys.",
        ],
    )


def build_openai_tools() -> List[Dict[str, Any]]:
    tools: List[Dict[str, Any]] = []

    for action in ACTION_REGISTRY.values():
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": action.name,
                    "description": action.purpose,
                    "parameters": action.input_schema,
                },
            }
        )

    tools.append(
        {
            "type": "function",
            "function": {
                "name": "respond_to_user",
                "description": "Produce the final user-facing response. Use only after all needed tool calls are complete.",
                "parameters": RespondToUserArgs.model_json_schema(),
            },
        }
    )

    return tools


def _format_examples(examples: List[RegistryExample]) -> str:
    if not examples:
        return "None."

    blocks: List[str] = []
    for example in examples:
        blocks.append(
            "\n".join(
                [
                    f"- Scenario: {example.scenario}",
                    f"  Input: {example.input}",
                    f"  Output: {example.output}",
                    f"  Notes: {example.notes or 'None'}",
                ]
            )
        )
    return "\n".join(blocks)


def build_system_prompt() -> str:
    registry = build_registry_bundle()

    ui_lines: List[str] = []
    for ui in registry.ui_components:
        ui_lines.append(
            "\n".join(
                [
                    f"UI component: {ui.name}",
                    f"Purpose: {ui.purpose}",
                    f"When to use: {ui.when_to_use}",
                    f"Notes: {', '.join(ui.notes) if ui.notes else 'None'}",
                    f"Examples:\n{_format_examples(ui.examples)}",
                ]
            )
        )

    action_lines: List[str] = []
    for action in registry.actions:
        action_lines.append(
            "\n".join(
                [
                    f"Action: {action.name}",
                    f"Purpose: {action.purpose}",
                    f"When to use: {action.when_to_use}",
                    f"Notes: {', '.join(action.notes) if action.notes else 'None'}",
                    f"Examples:\n{_format_examples(action.examples)}",
                ]
            )
        )

    return (
        "You are a digital front desk assistant for small hospitals and clinics.\n"
        "Your job is to help users search for care, see appointment slots, book or cancel appointments, and gather minimal context.\n"
        "If the user asks for anything outside this app's capabilities, refuse politely and briefly.\n\n"
        "Important operating rules:\n"
        "- Treat the patient as NOT registered or affiliated with any hospital.\n"
        "- Do not use any hidden state machine or hard-coded intent keywords.\n"
        "- Do not invent tools, UI components, or output fields that are not in the registry.\n"
        "- Use the tools as a ReAct loop: think, call a tool if needed, then continue until ready to answer.\n"
        "- Use at most one backend action per turn unless the model is explicitly gathering information.\n"
        "- When you are ready to answer the user, you MUST call respond_to_user.\n"
        "- Use picker when the user must choose among options.\n"
        "- Use alert when you need to confirm, inform, warn, or refuse.\n"
        "- Take as much information as possible from the user before performing actions.\n"
        "- For example: Ask some simple questions to gather symptoms and know more about their problems before you show appointment slots and book an appointment."
        " Mention that they can refuse to do so if they don't want to but it will help you to take better decisions.\n"
        "- For example: You can confirm your understanding of their problem with them and then proceed to actions.\n"
        "- User should think that they are talking to at an actual front desk.\n\n"
        "Registered UI components:\n"
        f"{chr(10).join(ui_lines)}\n\n"
        "Registered actions:\n"
        f"{chr(10).join(action_lines)}\n\n"
        "Registry rules:\n"
        f"{chr(10).join(f'- {rule}' for rule in registry.rules)}\n"
    )


def _register_defaults() -> None:
    register_ui_component(
        UIComponentSpec(
            name=AIUIComponent.ALERT.value,
            purpose="Show a short system message, confirmation, warning, or refusal.",
            when_to_use="Use when the user only needs a concise informational message or a decision confirmation.",
            data_model=AlertUI,
            notes=[
                "Keep the text short.",
                "Use the level field to convey severity.",
            ],
            examples=[
                RegistryExample(
                    scenario="Confirm an appointment",
                    input={
                        "title": "Appointment booked",
                        "message": "Your appointment is confirmed for 12 Apr 2026 at 10:30 AM.",
                        "level": "success",
                    },
                    output={
                        "component": "alert",
                        "data": {
                            "title": "Appointment booked",
                            "message": "Your appointment is confirmed for 12 Apr 2026 at 10:30 AM.",
                            "level": "success",
                        },
                    },
                ),
            ],
        )
    )

    register_ui_component(
        UIComponentSpec(
            name=AIUIComponent.PICKER.value,
            purpose="Show a list of choices that the user can pick from.",
            when_to_use="Use when you need the user to choose a hospital, doctor, appointment slot, or any other discrete option.",
            data_model=PickerUI,
            notes=[
                "Keep the option count manageable.",
                "Include stable values in option.meta when a later action needs exact identifiers.",
            ],
            examples=[
                RegistryExample(
                    scenario="Choose a slot",
                    input={
                        "title": "Choose a slot",
                        "prompt": "Pick one of the available appointment times.",
                        "options": [
                            {
                                "label": "Dr. Rao | 12 Apr 2026, 10:30 AM",
                                "value": "slot_1",
                            },
                        ],
                    },
                    output={
                        "component": "picker",
                        "data": {
                            "title": "Choose a slot",
                            "prompt": "Pick one of the available appointment times.",
                            "options": [
                                {
                                    "label": "Dr. Rao | 12 Apr 2026, 10:30 AM",
                                    "value": "slot_1",
                                },
                            ],
                        },
                    },
                )
            ],
        )
    )

    from app.controllers.agent_actions.find_appointment_slots import (
        execute_find_appointment_slots,
    )
    from app.controllers.agent_actions.book_appointment import execute_book_appointment
    from app.controllers.agent_actions.cancel_appointment import (
        execute_cancel_appointment,
    )
    from app.controllers.agent_actions.get_user_info import execute_get_user_info

    register_action(
        ActionSpec(
            name="find_appointment_slots",
            purpose="Search for available appointment slots across active hospitals and doctors.",
            when_to_use="Use when the user wants to book an appointment, browse available doctors, or choose a time.",
            input_model=LookupSlotsInput,
            output_model=LookupSlotsOutput,
            executor=execute_find_appointment_slots,
            notes=[
                "Prefer returning a picker-ready result.",
                "Use the patient's current conversation context, not inferred hospital affiliation.",
            ],
            examples=[
                RegistryExample(
                    scenario="Search available slots",
                    input={
                        "patient_id": 12,
                        "specialisation": "general",
                        "city": "Bengaluru",
                    },
                    output={
                        "summary": "Found 5 available slots.",
                        "options": [
                            {
                                "label": "Dr. Singh | 12 Apr 2026, 10:30 AM",
                                "value": "slot_1",
                            }
                        ],
                    },
                )
            ],
        )
    )

    register_action(
        ActionSpec(
            name="book_appointment",
            purpose="Create a new appointment using the selected doctor and slot.",
            when_to_use="Use after the user has selected a slot or explicitly provided all booking details.",
            input_model=BookAppointmentInput,
            output_model=BookAppointmentOutput,
            executor=execute_book_appointment,
            notes=[
                "Validate conflicts before booking.",
                "Use the slot metadata when booking from a picker.",
            ],
            examples=[
                RegistryExample(
                    scenario="Book a chosen slot",
                    input={
                        "patient_id": 12,
                        "doctor_id": 5,
                        "hospital_id": 2,
                        "department_id": 1,
                        "scheduled_at": "2026-04-12T10:30:00",
                    },
                    output={
                        "summary": "Appointment booked successfully.",
                        "appointment_id": 101,
                    },
                )
            ],
        )
    )

    register_action(
        ActionSpec(
            name="cancel_appointment",
            purpose="Cancel an existing appointment for the user.",
            when_to_use="Use when the user wants to cancel an appointment and has an appointment id or a directly resolvable appointment.",
            input_model=CancelAppointmentInput,
            output_model=CancelAppointmentOutput,
            executor=execute_cancel_appointment,
            examples=[
                RegistryExample(
                    scenario="Cancel an appointment",
                    input={
                        "appointment_id": 101,
                        "patient_id": 12,
                    },
                    output={
                        "summary": "Appointment cancelled successfully.",
                        "appointment_id": 101,
                    },
                )
            ],
        )
    )

    register_action(
        ActionSpec(
            name="get_user_info",
            purpose="Fetch the patient's basic profile and health profile for context.",
            when_to_use="Use when the assistant needs the user's details to complete a booking or to confirm profile information.",
            input_model=GetUserInfoInput,
            output_model=GetUserInfoOutput,
            executor=execute_get_user_info,
            notes=[
                "Do not surface any hospital affiliation as a reason to route the conversation.",
                "Return an unaffiliated patient context.",
            ],
            examples=[
                RegistryExample(
                    scenario="Fetch user profile",
                    input={"patient_id": 12},
                    output={
                        "summary": "Loaded patient information.",
                        "patient": {"patient_id": 12, "full_name": "Asha"},
                    },
                )
            ],
        )
    )


_register_defaults()
