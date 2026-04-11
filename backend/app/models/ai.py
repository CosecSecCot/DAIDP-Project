from __future__ import annotations

from datetime import date, datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional, Union, Annotated

from pydantic import BaseModel, ConfigDict, Field


class AIUIComponent(str, Enum):
    NONE = "none"
    ALERT = "alert"
    PICKER = "picker"


class AlertLevel(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"


class PickerOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: str
    description: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class AlertData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    message: str
    level: AlertLevel = AlertLevel.INFO
    details: Optional[str] = None


class PickerData(BaseModel):
    model_config = ConfigDict(extra="forbid")

    title: str
    prompt: str
    options: List[PickerOption]
    allow_multiple: bool = False
    empty_state_message: Optional[str] = None


class AlertUI(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component: Literal["alert"] = "alert"
    data: AlertData


class NoneUI(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component: Literal["none"] = "none"
    data: Optional[Dict[str, Any]] = None


class PickerUI(BaseModel):
    model_config = ConfigDict(extra="forbid")

    component: Literal["picker"] = "picker"
    data: PickerData


UIBlock = Annotated[Union[NoneUI, AlertUI, PickerUI], Field(discriminator="component")]


class ActionStatus(str, Enum):
    SUCCESS = "success"
    FAILED = "failed"


class ActionRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    status: ActionStatus
    summary: str
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Optional[Dict[str, Any]] = None
    error: Optional[str] = None


class AgentResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str
    ui: UIBlock
    actions: List[ActionRecord] = Field(default_factory=list)


class RespondToUserArgs(AgentResponse):
    model_config = ConfigDict(extra="forbid")


class ChatRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    chat_id: Optional[int] = None
    message: Union[str, Dict[str, Any]]


class ChatResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    chat_id: int
    message: str
    ui: UIBlock
    actions: List[ActionRecord] = Field(default_factory=list)


class ChatSessionResponse(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    user_id: int
    title: str
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class ChatHistoryMessage(BaseModel):
    model_config = ConfigDict(extra="forbid")

    id: int
    chat_id: Optional[int] = None
    user_id: int
    role: str
    content: Any
    extra: Optional[Dict[str, Any]] = None
    status: str
    timestamp: Optional[str] = None
    updated_at: Optional[str] = None


class PatientContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int
    full_name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    date_of_birth: Optional[date] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    blood_group: Optional[str] = None
    registered_hospital_id: Optional[int] = None
    is_affiliated_with_hospital: bool = False
    health_profile: Dict[str, Any] = Field(default_factory=dict)


class RegistryExample(BaseModel):
    model_config = ConfigDict(extra="forbid")

    scenario: str
    input: Dict[str, Any] = Field(default_factory=dict)
    output: Dict[str, Any] = Field(default_factory=dict)
    notes: Optional[str] = None


class RegistryEntry(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    purpose: str
    when_to_use: str
    notes: List[str] = Field(default_factory=list)
    examples: List[RegistryExample] = Field(default_factory=list)


class UIRegistryEntry(RegistryEntry):
    model_config = ConfigDict(extra="forbid")

    component_schema: Dict[str, Any] = Field(default_factory=dict)


class ActionRegistryEntry(RegistryEntry):
    model_config = ConfigDict(extra="forbid")

    input_schema: Dict[str, Any] = Field(default_factory=dict)
    output_schema: Dict[str, Any] = Field(default_factory=dict)


class RegistryBundle(BaseModel):
    model_config = ConfigDict(extra="forbid")

    ui_components: List[UIRegistryEntry] = Field(default_factory=list)
    actions: List[ActionRegistryEntry] = Field(default_factory=list)
    rules: List[str] = Field(default_factory=list)


class ToolCallRecord(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    arguments: Dict[str, Any] = Field(default_factory=dict)


class AIExecutionContext(BaseModel):
    model_config = ConfigDict(extra="forbid")

    user_id: int
    chat_id: int
    patient: PatientContext
    registry: RegistryBundle
    history_limit: int = 10


class LookupSlotsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int
    query: Optional[str] = None
    hospital_id: Optional[int] = None
    hospital_name: Optional[str] = None
    city: Optional[str] = None
    specialisation: Optional[str] = None
    preferred_date: Optional[date] = None
    limit: int = 10


class SlotOption(BaseModel):
    model_config = ConfigDict(extra="forbid")

    label: str
    value: str
    doctor_id: int
    doctor_name: str
    hospital_id: int
    hospital_name: str
    department_id: int
    scheduled_at: datetime
    description: Optional[str] = None
    meta: Dict[str, Any] = Field(default_factory=dict)


class LookupSlotsOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    options: List[SlotOption] = Field(default_factory=list)
    ui: Optional[PickerUI] = None


class BookAppointmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int
    doctor_id: int
    hospital_id: int
    department_id: Optional[int] = None
    scheduled_at: datetime
    duration_mins: int = 30
    notes: Optional[str] = None


class BookAppointmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    appointment_id: Optional[int] = None
    scheduled_at: Optional[datetime] = None
    doctor_id: Optional[int] = None
    hospital_id: Optional[int] = None


class CancelAppointmentInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    appointment_id: int
    patient_id: Optional[int] = None


class CancelAppointmentOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    appointment_id: int


class GetUserInfoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    patient_id: int


class GetUserInfoOutput(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str
    patient: PatientContext
