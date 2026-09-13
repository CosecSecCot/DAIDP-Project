import logging
from datetime import UTC, datetime
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from langgraph.graph.state import RunnableConfig
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import checkpoint
from app.db.database import get_db
from app.db.models import AppointmentSlot, Doctor, Document
from app.api.schema import ConversationCreate, ConversationMessage as ConversationMessageRequest

router = APIRouter(prefix="/conversations", tags=["conversations"])
logger = logging.getLogger(__name__)


def _assistant_text(state: dict) -> str | None:
    if state.get("status") == "needs_more_information":
        return state.get("followup_question") or state.get("assistant_reply")
    if state.get("status") == "guidance_ready":
        return state.get("guidance_disclaimer") or state.get("assistant_reply")
    return state.get("assistant_reply") or state.get("followup_question") or state.get("guidance_disclaimer")


async def _invoke(thread_id: str, message: str, document_ids: list[str], db: AsyncSession):
    if checkpoint.agent_graph is None:
        raise HTTPException(status_code=503, detail="Conversation graph is not initialized")
    config: RunnableConfig = {"configurable": {"thread_id": thread_id}}
    snapshot = await checkpoint.agent_graph.aget_state(config)
    previous = snapshot.values or {}
    transcript = list(previous.get("conversation", []))
    previous_reply = _assistant_text(previous)
    if previous_reply:
        transcript.append({"role": "assistant", "content": previous_reply})
    transcript.append({"role": "user", "content": message})

    selected_document_ids = list(dict.fromkeys([
        *previous.get("document_ids", []),
        *document_ids,
    ]))
    records = (await db.scalars(
        select(Document)
        .where(
            Document.id.in_(selected_document_ids),
            Document.processing_status == "ready",
        )
    )).all() if selected_document_ids else []
    document_catalog = [
        {"document_id": item.id, "filename": item.filename, "text": (item.extracted_text or "")[:12000]}
        for item in records
    ]
    patient_history = "Uploaded record context:\n" + "\n\n".join(
        f"{item.filename}: {(item.extracted_text or '')[:4000]}" for item in records[:3]
    ) if records else "No prior history."

    doctors = (await db.scalars(select(Doctor).where(Doctor.is_active.is_(True)).limit(100))).all()
    doctor_directory = [
        {"id": str(d.id), "name": d.display_name, "specialty": d.specialty, "clinic": d.clinic_name, "location": d.location, "bio": d.bio}
        for d in doctors
    ]
    slots = (await db.scalars(
        select(AppointmentSlot).where(
            AppointmentSlot.status == "available",
            AppointmentSlot.starts_at >= datetime.now(UTC),
        )
        .order_by(AppointmentSlot.starts_at).limit(100)
    )).all()
    available_slots = [
        {"id": str(slot.id), "doctor_id": str(slot.doctor_id), "doctor_name": next((doctor.display_name for doctor in doctors if doctor.id == slot.doctor_id), ""), "starts_at": slot.starts_at.isoformat(), "duration_minutes": str(slot.duration_minutes), "visit_type": slot.visit_type}
        for slot in slots
    ]
    state = {
        **previous,
        "user_message": message,
        "conversation": transcript,
        "patient_history": patient_history,
        "document_ids": selected_document_ids,
        "doctor_directory": doctor_directory,
        "document_catalog": document_catalog,
        "available_slots": available_slots,
        "followup_rounds": previous.get("followup_rounds", 0),
    }
    try:
        result = await checkpoint.agent_graph.ainvoke(state, config=config)
    except RuntimeError as exc:
        logger.exception("Conversation graph setup failed")
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    except Exception as exc:
        logger.exception("Conversation agent failed")
        raise HTTPException(status_code=502, detail="A conversation agent could not complete this turn") from exc
    return _response(thread_id, result)


def _response(thread_id: str, state: dict):
    transcript = state.get("conversation", [])
    assistant_text = _assistant_text(state)
    status = state.get("status", "conversation_active")
    if assistant_text:
        transcript = [*transcript, {"role": "assistant", "content": assistant_text}]
    return {
        "conversation_id": thread_id,
        "document_ids": state.get("document_ids", []),
        "status": status,
        "agent": state.get("intent", "intake"),
        "message": assistant_text,
        "intake_summary": state.get("intake_summary"),
        "missing_fields": state.get("missing_fields", []),
        "guidance": ({"urgency": state.get("urgency"), "preliminary_steps": state.get("preliminary_steps"), "disclaimer": state.get("guidance_disclaimer")} if state.get("has_guidance") and state.get("guidance_disclaimer") and status != "recommendations_ready" else None),
        "doctor_recommendations": state.get("doctor_recommendations", []) if status == "recommendations_ready" else [],
        "source_documents": state.get("source_documents", []) if state.get("intent") == "documents" else [],
        "available_slots": state.get("available_slots", []) if status == "awaiting_slot_choice" else [],
        "followup_rounds": state.get("followup_rounds", 0),
        "messages": transcript,
    }


@router.post("")
async def create_conversation(payload: ConversationCreate, db: AsyncSession = Depends(get_db)):
    return await _invoke(uuid4().hex, payload.message, payload.document_ids, db)


@router.post("/{conversation_id}/messages")
async def add_message(conversation_id: str, payload: ConversationMessageRequest, db: AsyncSession = Depends(get_db)):
    return await _invoke(conversation_id, payload.message, payload.document_ids, db)


@router.get("/{conversation_id}")
async def get_conversation(conversation_id: str):
    if checkpoint.agent_graph is None:
        raise HTTPException(status_code=503, detail="Conversation graph is not initialized")
    config: RunnableConfig = {"configurable": {"thread_id": conversation_id}}
    snapshot = await checkpoint.agent_graph.aget_state(config)
    if not snapshot.values:
        raise HTTPException(status_code=404, detail="Conversation is no longer available")
    return _response(conversation_id, snapshot.values)
