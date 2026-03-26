from sqlalchemy import Column, Integer, String, Text, DateTime, Date, Enum as SAEnum, Boolean
from app.config.database import Base
import enum

class AppointmentType(str, enum.Enum):
    ONLINE   = "online"
    WALK_IN  = "walk_in"

class AppointmentStatus(str, enum.Enum):
    SCHEDULED = "scheduled"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    NO_SHOW   = "no_show"

class BookedBy(str, enum.Enum):
    PATIENT = "patient"
    STAFF   = "staff"
    AI      = "ai"

class AppointmentFrequency(str, enum.Enum):
    DAILY   = "daily"
    WEEKLY  = "weekly"
    MONTHLY = "monthly"

class WaitlistStatus(str, enum.Enum):
    WAITING = "waiting"
    OFFERED = "offered"
    EXPIRED = "expired"

class Appointment(Base):
    __tablename__ = "appointments"
    id                 = Column(Integer, primary_key=True, autoincrement=True)
    patient_id         = Column(Integer, nullable=False)
    doctor_id          = Column(Integer, nullable=False)
    hospital_id        = Column(Integer, nullable=False)
    department_id      = Column(Integer, nullable=False)
    series_id          = Column(Integer)
    scheduled_at       = Column(DateTime, nullable=False)
    duration_mins      = Column(Integer, default=30)
    type               = Column(SAEnum(AppointmentType), nullable=False)
    status             = Column(SAEnum(AppointmentStatus), default=AppointmentStatus.SCHEDULED)
    booked_by          = Column(SAEnum(BookedBy), nullable=False)
    booked_by_staff_id = Column(Integer)
    notes              = Column(Text)

class RecurringAppointmentSeries(Base):
    __tablename__ = "recurring_appointment_series"
    id                = Column(Integer, primary_key=True, autoincrement=True)
    patient_id        = Column(Integer, nullable=False)
    doctor_id         = Column(Integer, nullable=False)
    hospital_id       = Column(Integer, nullable=False)
    frequency         = Column(SAEnum(AppointmentFrequency), nullable=False)
    start_date        = Column(Date, nullable=False)
    end_date          = Column(Date)
    total_occurrences = Column(Integer)

class Waitlist(Base):
    __tablename__ = "waitlist"
    id             = Column(Integer, primary_key=True, autoincrement=True)
    patient_id     = Column(Integer, nullable=False)
    doctor_id      = Column(Integer, nullable=False)
    hospital_id    = Column(Integer, nullable=False)
    preferred_date = Column(Date)
    priority       = Column(Integer, default=0)
    status         = Column(SAEnum(WaitlistStatus), default=WaitlistStatus.WAITING)