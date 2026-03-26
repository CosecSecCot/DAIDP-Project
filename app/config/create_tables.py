from app.config.database import engine, Base

from app.models.hospital import Hospital, Department
from app.models.staff import Staff
from app.models.doctor import Doctor, DoctorHospitalAffiliation, DoctorAvailability
from app.models.patient import Patient, PatientHealthProfile
from app.models.appointment import Appointment, RecurringAppointmentSeries, Waitlist
from app.models.medical import MedicalRecord, Diagnosis, LabTest, Document
from app.models.prescription import Prescription, PrescriptionItem
from app.models.billing import Invoice, Payment

def create_tables():
    print("Creating tables...")
    Base.metadata.create_all(bind=engine)
    print("All tables created successfully.")

if __name__ == "__main__":
    create_tables()