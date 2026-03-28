from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from decimal import Decimal

from app.models.billing import Invoice, Payment, InvoiceStatus
from app.schemas.billing import InvoiceCreate, InvoiceUpdate, PaymentCreate


# ── Helpers ───────────────────────────────────────────────────────────────────

def calculate_final_amount(total: float, discount: float, tax: float) -> float:
    total    = Decimal(str(total))
    discount = Decimal(str(discount))
    tax      = Decimal(str(tax))
    return float((total - discount) + ((total - discount) * tax / 100))


def get_invoice_by_id(invoice_id: int, db: Session):
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invoice not found"
        )
    return invoice


def update_invoice_status(invoice: Invoice, db: Session):
    payments = db.query(Payment).filter(
        Payment.invoice_id == invoice.id
    ).all()

    total_paid = sum(float(p.amount_paid) for p in payments)

    if total_paid <= 0:
        invoice.status = InvoiceStatus.UNPAID
    elif total_paid >= float(invoice.final_amount):
        invoice.status = InvoiceStatus.PAID
    else:
        invoice.status = InvoiceStatus.PARTIAL

    db.commit()


# ── Invoices ──────────────────────────────────────────────────────────────────

def create_invoice(data: InvoiceCreate, db: Session):
    existing = db.query(Invoice).filter(
        Invoice.appointment_id == data.appointment_id
    ).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="An invoice already exists for this appointment"
        )

    final_amount = calculate_final_amount(
        data.total_amount,
        data.discount or 0,
        data.tax or 0
    )

    invoice = Invoice(
        appointment_id = data.appointment_id,
        patient_id     = data.patient_id,
        total_amount   = data.total_amount,
        discount       = data.discount or 0,
        tax            = data.tax or 0,
        final_amount   = final_amount
    )
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    return invoice


def get_all_invoices_by_patient(patient_id: int, db: Session):
    return db.query(Invoice).filter(
        Invoice.patient_id == patient_id
    ).order_by(Invoice.created_at.desc()).all()


def get_invoice(invoice_id: int, db: Session):
    return get_invoice_by_id(invoice_id, db)


def get_invoice_by_appointment(appointment_id: int, db: Session):
    invoice = db.query(Invoice).filter(
        Invoice.appointment_id == appointment_id
    ).first()
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No invoice found for this appointment"
        )
    return invoice


def update_invoice(invoice_id: int, data: InvoiceUpdate, db: Session):
    invoice = get_invoice_by_id(invoice_id, db)

    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a fully paid invoice"
        )

    if data.discount is not None:
        invoice.discount = data.discount
    if data.tax is not None:
        invoice.tax = data.tax

    invoice.final_amount = calculate_final_amount(
        float(invoice.total_amount),
        float(invoice.discount),
        float(invoice.tax)
    )

    if data.status is not None:
        invoice.status = data.status

    db.commit()
    db.refresh(invoice)
    return invoice


# ── Payments ──────────────────────────────────────────────────────────────────

def make_payment(invoice_id: int, data: PaymentCreate, db: Session):
    invoice = get_invoice_by_id(invoice_id, db)

    if invoice.status == InvoiceStatus.PAID:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice is already fully paid"
        )

    payments     = db.query(Payment).filter(Payment.invoice_id == invoice_id).all()
    total_paid   = sum(float(p.amount_paid) for p in payments)
    remaining    = float(invoice.final_amount) - total_paid

    if data.amount_paid > remaining:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Amount exceeds remaining balance of {remaining:.2f}"
        )

    payment = Payment(
        invoice_id      = invoice_id,
        amount_paid     = data.amount_paid,
        payment_method  = data.payment_method,
        transaction_ref = data.transaction_ref,
        notes           = data.notes
    )
    db.add(payment)
    db.commit()
    db.refresh(payment)

    update_invoice_status(invoice, db)

    return payment


def get_payments_by_invoice(invoice_id: int, db: Session):
    get_invoice_by_id(invoice_id, db)
    return db.query(Payment).filter(
        Payment.invoice_id == invoice_id
    ).order_by(Payment.paid_at).all()


def get_payment_by_id(invoice_id: int, payment_id: int, db: Session):
    get_invoice_by_id(invoice_id, db)
    payment = db.query(Payment).filter(
        Payment.id         == payment_id,
        Payment.invoice_id == invoice_id
    ).first()
    if not payment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Payment not found"
        )
    return payment