from pydantic import BaseModel
from enum import Enum
from typing import Optional
from datetime import datetime


class InvoiceStatus(str, Enum):
    UNPAID  = "unpaid"
    PARTIAL = "partial"
    PAID    = "paid"


class PaymentMethod(str, Enum):
    CASH = "cash"
    CARD = "card"
    UPI  = "upi"


# ── Invoice ───────────────────────────────────────────────────────────────────

class InvoiceCreate(BaseModel):
    appointment_id : int
    patient_id     : int
    total_amount   : float
    discount       : Optional[float] = 0.0
    tax            : Optional[float] = 0.0


class InvoiceUpdate(BaseModel):
    discount : Optional[float]        = None
    tax      : Optional[float]        = None
    status   : Optional[InvoiceStatus] = None


class InvoiceResponse(BaseModel):
    id             : int
    appointment_id : int
    patient_id     : int
    total_amount   : float
    discount       : float
    tax            : float
    final_amount   : float
    status         : InvoiceStatus
    created_at     : Optional[datetime]

    class Config:
        from_attributes = True


# ── Payment ───────────────────────────────────────────────────────────────────

class PaymentCreate(BaseModel):
    amount_paid     : float
    payment_method  : PaymentMethod
    transaction_ref : Optional[str] = None
    notes           : Optional[str] = None


class PaymentResponse(BaseModel):
    id              : int
    invoice_id      : int
    amount_paid     : float
    payment_method  : PaymentMethod
    paid_at         : Optional[datetime]
    transaction_ref : Optional[str]
    notes           : Optional[str]

    class Config:
        from_attributes = True