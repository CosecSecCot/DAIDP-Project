from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from typing import List

from app.config.database import get_db
from app.config.roles import admin_only, admin_doctor_staff, any_authenticated
from app.schemas.billing import (
    InvoiceCreate, InvoiceUpdate, InvoiceResponse,
    PaymentCreate, PaymentResponse
)
from app.controllers.billing_controller import (
    create_invoice, get_all_invoices_by_patient,
    get_invoice, get_invoice_by_appointment, update_invoice,
    make_payment, get_payments_by_invoice, get_payment_by_id
)

router = APIRouter(tags=["Billing"])


# ── Invoices ──────────────────────────────────────────────────────────────────

# Only admin and staff can create an invoice
@router.post("/invoices/", response_model=InvoiceResponse, status_code=201)
def create(
    data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return create_invoice(data, db)


# Admin, doctor, staff can get invoice by id
@router.get("/invoices/{invoice_id}", response_model=InvoiceResponse)
def get_one(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_invoice(invoice_id, db)


# All invoices for a patient
@router.get("/invoices/patient/{patient_id}", response_model=List[InvoiceResponse])
def by_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_all_invoices_by_patient(patient_id, db)


# Invoice for a specific appointment
@router.get("/invoices/appointment/{appointment_id}", response_model=InvoiceResponse)
def by_appointment(
    appointment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_invoice_by_appointment(appointment_id, db)


# Only admin and staff can update an invoice
@router.put("/invoices/{invoice_id}", response_model=InvoiceResponse)
def update(
    invoice_id: int,
    data: InvoiceUpdate,
    db: Session = Depends(get_db),
    current_user = Depends(admin_doctor_staff)
):
    return update_invoice(invoice_id, data, db)


# ── Payments ──────────────────────────────────────────────────────────────────

# Anyone can make a payment
@router.post("/invoices/{invoice_id}/payments/", response_model=PaymentResponse, status_code=201)
def pay(
    invoice_id: int,
    data: PaymentCreate,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return make_payment(invoice_id, data, db)


# Admin, doctor, staff can see all payments for an invoice
@router.get("/invoices/{invoice_id}/payments/", response_model=List[PaymentResponse])
def list_payments(
    invoice_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_payments_by_invoice(invoice_id, db)


# Get a specific payment
@router.get("/invoices/{invoice_id}/payments/{payment_id}", response_model=PaymentResponse)
def get_one_payment(
    invoice_id: int,
    payment_id: int,
    db: Session = Depends(get_db),
    current_user = Depends(any_authenticated)
):
    return get_payment_by_id(invoice_id, payment_id, db)