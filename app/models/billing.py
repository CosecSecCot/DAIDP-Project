from sqlalchemy import Column, String, Integer, Text, DateTime, Numeric, Enum as SAEnum
from app.config.database import Base
import enum

class InvoiceStatus(str, enum.Enum):
    UNPAID  = "unpaid"
    PARTIAL = "partial"
    PAID    = "paid"

class PaymentMethod(str, enum.Enum):
    CASH = "cash"
    CARD = "card"
    UPI  = "upi"

class Invoice(Base):
    __tablename__ = "invoices"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    appointment_id = Column(Integer, nullable=False, unique=True)
    patient_id     = Column(Integer, nullable=False)
    total_amount   = Column(Numeric(10, 2), nullable=False)
    discount       = Column(Numeric(10, 2), default=0)
    tax            = Column(Numeric(10, 2), default=0)
    final_amount   = Column(Numeric(10, 2), nullable=False)
    status         = Column(SAEnum(InvoiceStatus), default=InvoiceStatus.UNPAID)

class Payment(Base):
    __tablename__ = "payments"
    id              = Column(Integer, primary_key=True, autoincrement=True)
    invoice_id      = Column(Integer, nullable=False)
    amount_paid     = Column(Numeric(10, 2), nullable=False)
    payment_method  = Column(SAEnum(PaymentMethod), nullable=False)
    paid_at         = Column(DateTime)
    transaction_ref = Column(String(150))
    notes           = Column(Text)