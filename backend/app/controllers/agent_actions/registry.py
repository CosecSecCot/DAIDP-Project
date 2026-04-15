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
    executor: Callable[[Any], Any]
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
        notes_str = "\n".join(f"- {actn}" for actn in action.notes)
        tools.append(
            {
                "type": "function",
                "function": {
                    "name": action.name,
                    "description": f"Purpose:\n{action.purpose}\n"
                    f"When to use:\n{action.when_to_use}\n"
                    f"Notes:\n{notes_str}",
                    "parameters": action.input_schema,
                },
            }
        )

    tools.append(
        {
            "type": "function",
            "function": {
                "name": "respond_to_user",
                "description": "Produce the final user-facing response. Use only after all needed tool calls are complete, when you need to ask a few questions or acknowledged the user.",
                "parameters": RespondToUserArgs.model_json_schema(),
            },
        }
    )

    return tools


def build_plain_chat_tools() -> List[Dict[str, Any]]:
    return [
        {
            "type": "function",
            "function": {
                "name": "respond_to_user",
                "description": "Produce the final user-facing response. Use only after you have asked a few simple intake questions or acknowledged the user.",
                "parameters": RespondToUserArgs.model_json_schema(),
            },
        }
    ]


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


def build_system_prompt(*, warmup_mode: bool = False) -> str:
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
        # "- Use at most one backend action per turn unless the model is explicitly gathering information.\n"
        "- Prefer one backend action per turn unless multiple steps are required to complete the user's request.\n"
        "- When you are ready to answer the user, you MUST call respond_to_user.\n"
        "- Use picker when the user must choose among options.\n"
        "- Use alert when you need to confirm, inform, warn, or refuse.\n"
        "- In the beginning of a chat, keep the conversation plain and natural.\n"
        "- Your primary goal is to understand the user's problem with sufficient context before taking action.\n"
        "- Prefer gathering sufficient useful context (not excessive) that would help a doctor understand the case before acting, unless user intent is explicit.\n"
        "- If the user is describing symptoms, issues, or vague problems, ask 1-2 short clarifying questions before calling tools.\n"
        "- For medical/problem descriptions, prefer collecting richer context (2-4 short questions if needed), not just one.\n"
        "- Balance depth with user friction. Stop when context is sufficient, not maximal.\n"
        "- Do not delay actions when sufficient information is already available.\n"
        "- Booking an appointment is NOT an immediate action. It requires sufficient context about the user's problem.\n"
        "- If the user wants to book an appointment, first gather relevant context that would be useful for a doctor.\n"
        "- Ask focused follow-up questions such as symptoms, duration, severity, prior history, or urgency.\n"
        "- Only proceed to search slots or booking after sufficient context is collected.\n"
        "- Do not rush into slot search unless the user explicitly skips questions.\n"
        "- If the user explicitly says to skip questions or proceed quickly, reduce questions and act.\n"
        "- Ask a short follow-up question or two before showing appointment slots.\n"
        "- Only ask simple, human front-desk style questions at first, such as the main problem, duration, or urgency.\n"
        "- Tell the user they can skip the questions if they prefer, but the questions help you guide them better.\n"
        "- Do not show a picker in the warm-up phase unless the user explicitly asks to see options right away.\n"
        "- If the user intent is explicit (booking doesn't count as explicit intent, unless enforced by user), act immediately instead of waiting for more context.\n"
        "- User should think that they are talking to an actual front desk assistant.\n\n"

        "--- Documents handling ---\n"
        "- Users may ask to view, open, or understand their medical documents or reports.\n"
        "- Use get_user_appointment_documents to fetch available documents.\n"
        "- If the user refers to a specific document (e.g., 'latest report', 'blood test', 'MRI'), first fetch documents and then identify the most relevant one.\n"
        "- Prefer the most recent document when the user says 'latest' or does not specify.\n"
        "- Use file names and document types to infer relevance (e.g., 'blood', 'MRI', 'prescription').\n"
        "- If the user wants to open or view a document, retrieve its file using the appropriate endpoint.\n"
        "- If the user wants a summary or explanation, retrieve the document content and summarize it clearly.\n"
        "- Do not hallucinate document content. Always retrieve before summarizing.\n"
        "- Document interactions may require multiple DIFFERENT actions, but do not repeat the same action unless new information is needed.\n"
        "- If relevant documents are successfully retrieved, do NOT call the same action again. Proceed to respond_to_user.\n\n"
        "- To understand or summarize a document, you MUST first use read_document.\n"
        "- Do NOT guess or hallucinate document contents.\n"
        "- After reading the document, summarize the key medical information clearly.\n"
        "- After a successful read_document call, DO NOT call read_document again for the same document.\n"
        "- Proceed directly to respond_to_user with a summary or explanation.\n"
        "- If the text is long, focus on important medical values, diagnoses, and findings.\n\n"

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
    from app.controllers.agent_actions.get_user_appointments import (
        execute_get_user_appointments,
        GetUserAppointmentsInput,
        GetUserAppointmentsOutput
    )
    from app.controllers.agent_actions.book_appointment import execute_book_appointment
    from app.controllers.agent_actions.cancel_appointment import (
        execute_cancel_appointment,
    )
    from app.controllers.agent_actions.get_user_documents import (
        execute_get_user_appointment_documents,
        GetUserAppointmentDocumentsInput,
        GetUserAppointmentDocumentsOutput
    )
    from app.controllers.agent_actions.read_document import (
        execute_read_document,
        ReadDocumentInput,
        ReadDocumentOutput
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
            name="get_user_appointments",
            purpose="Fetch all appointments for a user to help identify, review, or manage them. Use this to see appointments when appointment_id is not provided.",
            when_to_use="Use when the user refers to an appointment without providing an appointment_id (e.g., by doctor name, time, or date), or when the assistant needs to resolve which appointment to act on.",
            input_model=GetUserAppointmentsInput,
            output_model=GetUserAppointmentsOutput,
            executor=execute_get_user_appointments,
            notes=[
                "Use this before cancel_appointment if the appointment_id is unknown.",
                "Return all appointments and let the assistant match based on context like doctor name or time.",
                "Do not assume or hallucinate appointment_id.",
            ],
            examples=[
                RegistryExample(
                    scenario="Fetch all appointments for a user",
                    input={
                        "patient_id": 12
                    },
                    output={
                        "summary": "Found 2 appointments for the user.",
                        "appointments": [
                            {
                                "appointment_id": 101,
                                "doctor_id": 5,
                                "scheduled_at": "2026-04-15T10:00:00",
                                "status": "scheduled"
                            },
                            {
                                "appointment_id": 102,
                                "doctor_id": 8,
                                "scheduled_at": "2026-04-16T14:30:00",
                                "status": "scheduled"
                            }
                        ]
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
            name="get_user_appointment_documents",
            purpose="Fetch all documents uploaded for the user's appointments.",
            when_to_use="Use when the user asks to view, list, or access their medical documents or reports.",
            input_model=GetUserAppointmentDocumentsInput,
            output_model=GetUserAppointmentDocumentsOutput,
            executor=execute_get_user_appointment_documents,
            notes=[
                "Returns documents sorted by most recent.",
                "Does not include file content, only metadata."
            ],
            examples=[
                RegistryExample(
                    scenario="User asks to see their reports",
                    input={"patient_id": 3},
                    output={
                        "summary": "Found 2 appointment document(s).",
                        "documents": [
                            {
                                "id": 1,
                                "file_name": "blood_report.pdf"
                            }
                        ]
                    }
                )
            ],
        )
    )

    register_action(
        ActionSpec(
            name="read_document",
            purpose="Read and extract text from a medical document (PDF or image).",
            when_to_use="Use when the user wants to view, understand, or summarize a document.",
            input_model=ReadDocumentInput,
            output_model=ReadDocumentOutput,
            executor=execute_read_document,
            notes=[
                "Supports PDF and image files.",
                "Returns extracted text (may be truncated).",
                "Use before summarizing document contents.",
            ],
            examples=[
                RegistryExample(
                    scenario="Read a report",
                    input={
                        "patient_id": 3,
                        "document_id": 12
                    },
                    output={
                        "summary": "Document text extracted successfully.",
                        "text": "Hemoglobin: 13.5 g/dL...",
                        "truncated": False
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
