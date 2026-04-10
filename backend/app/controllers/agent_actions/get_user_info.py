from __future__ import annotations

from app.config.database import SessionLocal
from app.controllers.agent_actions.common import load_patient_and_profile, normalize_patient_context
from app.models.ai import GetUserInfoInput, GetUserInfoOutput, PatientContext


def execute_get_user_info(input_data: GetUserInfoInput) -> GetUserInfoOutput:
    db = SessionLocal()
    try:
        patient, health_profile = load_patient_and_profile(input_data.patient_id, db)
        if patient is None:
            return GetUserInfoOutput(
                summary="Patient not found.",
                patient=PatientContext(patient_id=input_data.patient_id),
            )

        payload = normalize_patient_context(patient)
        payload["health_profile"] = health_profile

        return GetUserInfoOutput(
            summary="Loaded patient information.",
            patient=PatientContext.model_validate(payload),
        )
    finally:
        db.close()

