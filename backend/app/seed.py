from .config.database import SessionLocal, engine, Base
from .models.hospital import Hospital, Department, HospitalType
from .models.staff import Staff, StaffRole
from .models.doctor import Doctor, DoctorHospitalAffiliation, DoctorAvailability, AffiliationRole
from .models.patient import Patient, PatientHealthProfile, Gender
from .models.appointment import Appointment, AppointmentType, AppointmentStatus, BookedBy, RecurringAppointmentSeries, Waitlist, AppointmentFrequency, WaitlistStatus
from .models.medical import MedicalRecord, Diagnosis, LabTest, Document, DiagnosisSeverity, LabTestStatus, DocumentType, UploadedBy
from .models.prescription import Prescription, PrescriptionItem
from .models.billing import Invoice, Payment, InvoiceStatus, PaymentMethod
from datetime import datetime, date, timedelta
import random

def seed_database():
    db = SessionLocal()
    try:
        # Drop and recreate all tables to ensure schema is up to date
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)

        # Seed Hospitals
        hospitals = [
            Hospital(
                name="City General Hospital",
                address="123 Main St, Cityville",
                city="Cityville",
                phone="555-0101",
                email="info@citygeneral.com",
                type=HospitalType.HOSPITAL
            ),
            Hospital(
                name="Downtown Clinic",
                address="456 Elm St, Downtown",
                city="Downtown",
                phone="555-0202",
                email="contact@downtownclinic.com",
                type=HospitalType.CLINIC
            )
        ]
        db.add_all(hospitals)
        db.commit()

        # Seed Departments
        departments = [
            Department(hospital_id=1, name="Cardiology", description="Heart care"),
            Department(hospital_id=1, name="Neurology", description="Brain and nerves"),
            Department(hospital_id=2, name="General Medicine", description="Primary care")
        ]
        db.add_all(departments)
        db.commit()

        # Seed Staff
        staff_members = [
            Staff(
                hospital_id=1,
                full_name="Alice Johnson",
                role=StaffRole.RECEPTIONIST,
                email="alice@citygeneral.com",
                hashed_password="hashedpassword",
                phone="555-1001"
            ),
            Staff(
                hospital_id=1,
                full_name="Bob Smith",
                role=StaffRole.NURSE,
                email="bob@citygeneral.com",
                hashed_password="hashedpassword",
                phone="555-1002"
            ),
            Staff(
                hospital_id=2,
                full_name="Carol Davis",
                role=StaffRole.ADMIN,
                email="carol@downtownclinic.com",
                hashed_password="hashedpassword",
                phone="555-2001"
            )
        ]
        db.add_all(staff_members)
        db.commit()

        # Seed Doctors
        doctors = [
            Doctor(
                full_name="Dr. Emily Carter",
                email="emily.carter@citygeneral.com",
                hashed_password="hashedpassword",
                phone="555-3001",
                specialisation="Cardiology",
                qualification="MD",
                years_of_experience=10,
                consultation_fee=150.00
            ),
            Doctor(
                full_name="Dr. John Lee",
                email="john.lee@downtownclinic.com",
                hashed_password="hashedpassword",
                phone="555-3002",
                specialisation="General Medicine",
                qualification="MBBS",
                years_of_experience=8,
                consultation_fee=100.00
            )
        ]
        db.add_all(doctors)
        db.commit()

        # Seed Doctor Affiliations
        affiliations = [
            DoctorHospitalAffiliation(
                doctor_id=1,
                hospital_id=1,
                department_id=1,
                role=AffiliationRole.RESIDENT,
                joined_date=date(2020, 1, 1)
            ),
            DoctorHospitalAffiliation(
                doctor_id=2,
                hospital_id=2,
                department_id=3,
                role=AffiliationRole.VISITING,
                joined_date=date(2021, 6, 1)
            )
        ]
        db.add_all(affiliations)
        db.commit()

        # Seed Doctor Availability
        availabilities = [
            DoctorAvailability(
                doctor_id=1,
                hospital_id=1,
                day_of_week=1,  # Monday
                start_time="09:00",
                end_time="17:00",
                slot_duration_mins=30
            ),
            DoctorAvailability(
                doctor_id=2,
                hospital_id=2,
                day_of_week=2,  # Tuesday
                start_time="10:00",
                end_time="16:00",
                slot_duration_mins=45
            )
        ]
        db.add_all(availabilities)
        db.commit()

        # Seed Patients
        patients = [
            Patient(
                full_name="Patient One",
                email="patient1@example.com",
                hashed_password="hashedpassword",
                date_of_birth=date(1985, 5, 15),
                gender=Gender.MALE,
                phone="555-4001",
                address="789 Oak St",
                blood_group="O+",
                registered_hospital_id=1
            ),
            Patient(
                full_name="Patient Two",
                email="patient2@example.com",
                hashed_password="hashedpassword",
                date_of_birth=date(1990, 8, 20),
                gender=Gender.FEMALE,
                phone="555-4002",
                address="321 Pine St",
                blood_group="A-",
                registered_hospital_id=2
            )
        ]
        db.add_all(patients)
        db.commit()

        # Seed Patient Health Profiles
        profiles = [
            PatientHealthProfile(
                patient_id=1,
                known_allergies="Penicillin",
                chronic_conditions="Hypertension",
                emergency_contact_name="Relative One",
                emergency_contact_phone="555-5001"
            ),
            PatientHealthProfile(
                patient_id=2,
                known_allergies=None,
                chronic_conditions="Diabetes",
                emergency_contact_name="Relative Two",
                emergency_contact_phone="555-5002"
            )
        ]
        db.add_all(profiles)
        db.commit()

        # Seed Appointments
        appointments = [
            Appointment(
                patient_id=1,
                doctor_id=1,
                hospital_id=1,
                department_id=1,
                scheduled_at=datetime.now() + timedelta(days=1),
                duration_mins=30,
                type=AppointmentType.WALK_IN,
                status=AppointmentStatus.SCHEDULED,
                booked_by=BookedBy.PATIENT,
                notes="Routine checkup"
            ),
            Appointment(
                patient_id=2,
                doctor_id=2,
                hospital_id=2,
                department_id=3,
                scheduled_at=datetime.now() + timedelta(days=2),
                duration_mins=45,
                type=AppointmentType.ONLINE,
                status=AppointmentStatus.SCHEDULED,
                booked_by=BookedBy.STAFF,
                booked_by_staff_id=3
            )
        ]
        db.add_all(appointments)
        db.commit()

        # Seed Recurring Appointment Series
        recurring_series = [
            RecurringAppointmentSeries(
                patient_id=1,
                doctor_id=1,
                hospital_id=1,
                department_id=1,
                frequency=AppointmentFrequency.WEEKLY,
                start_date=date.today(),
                end_date=date.today() + timedelta(weeks=4),
                total_occurrences=4,
                duration_mins=30,
                start_time="10:00",
                type=AppointmentType.WALK_IN,
                notes="Weekly checkup series"
            )
        ]
        db.add_all(recurring_series)
        db.commit()

        # Seed Waitlist
        waitlist_entries = [
            Waitlist(
                patient_id=2,
                doctor_id=2,
                hospital_id=2,
                preferred_date=date.today() + timedelta(days=3),
                priority=1,
                status=WaitlistStatus.WAITING
            )
        ]
        db.add_all(waitlist_entries)
        db.commit()

        # Seed Medical Records
        records = [
            MedicalRecord(
                appointment_id=1,
                patient_id=1,
                doctor_id=1,
                visit_date=date.today(),
                presenting_complaints="Chest pain",
                notes="Patient stable",
                follow_up_date=date.today() + timedelta(days=7)
            ),
            MedicalRecord(
                appointment_id=2,
                patient_id=2,
                doctor_id=2,
                visit_date=date.today(),
                presenting_complaints="Fever",
                notes="Prescribed medication",
                follow_up_date=None
            )
        ]
        db.add_all(records)
        db.commit()

        # Seed Diagnoses
        diagnoses = [
            Diagnosis(
                record_id=1,
                icd_code="I10",
                description="Essential hypertension",
                severity=DiagnosisSeverity.MODERATE,
                is_chronic=True
            ),
            Diagnosis(
                record_id=2,
                icd_code="J00",
                description="Acute nasopharyngitis",
                severity=DiagnosisSeverity.MILD,
                is_chronic=False
            )
        ]
        db.add_all(diagnoses)
        db.commit()

        # Seed Lab Tests
        lab_tests = [
            LabTest(
                record_id=1,
                patient_id=1,
                test_name="Blood Pressure",
                ordered_at=datetime.now(),
                result="120/80",
                result_uploaded_at=datetime.now(),
                status=LabTestStatus.COMPLETED,
                notes="Normal"
            ),
            LabTest(
                record_id=2,
                patient_id=2,
                test_name="Blood Sugar",
                ordered_at=datetime.now(),
                result="140 mg/dL",
                result_uploaded_at=None,
                status=LabTestStatus.PENDING,
                notes="Awaiting results"
            )
        ]
        db.add_all(lab_tests)
        db.commit()

        # Seed Documents
        documents = [
            Document(
                patient_id=1,
                record_id=1,
                uploaded_by=UploadedBy.DOCTOR,
                file_name="report.pdf",
                file_url="/uploads/report.pdf",
                document_type=DocumentType.REPORT
            ),
            Document(
                patient_id=2,
                record_id=2,
                uploaded_by=UploadedBy.STAFF,
                file_name="scan.jpg",
                file_url="/uploads/scan.jpg",
                document_type=DocumentType.SCAN
            )
        ]
        db.add_all(documents)
        db.commit()

        # Seed Prescriptions
        prescriptions = [
            Prescription(
                record_id=1,
                patient_id=1,
                doctor_id=1,
                issued_at=datetime.now(),
                notes="Take as directed",
                is_active=True
            ),
            Prescription(
                record_id=2,
                patient_id=2,
                doctor_id=2,
                issued_at=datetime.now(),
                notes="Complete course",
                is_active=True
            )
        ]
        db.add_all(prescriptions)
        db.commit()

        # Seed Prescription Items
        items = [
            PrescriptionItem(
                prescription_id=1,
                medicine_name="Lisinopril",
                dosage="10mg",
                frequency="Once daily",
                duration="30 days",
                instructions="With food"
            ),
            PrescriptionItem(
                prescription_id=2,
                medicine_name="Paracetamol",
                dosage="500mg",
                frequency="Every 6 hours",
                duration="5 days",
                instructions="As needed for pain"
            )
        ]
        db.add_all(items)
        db.commit()

        # Seed Invoices
        invoices = [
            Invoice(
                appointment_id=1,
                patient_id=1,
                total_amount=150.00,
                discount=0.00,
                tax=15.00,
                final_amount=165.00,
                status=InvoiceStatus.UNPAID
            ),
            Invoice(
                appointment_id=2,
                patient_id=2,
                total_amount=100.00,
                discount=10.00,
                tax=9.00,
                final_amount=99.00,
                status=InvoiceStatus.PAID
            )
        ]
        db.add_all(invoices)
        db.commit()

        # Seed Payments
        payments = [
            Payment(
                invoice_id=2,
                amount_paid=99.00,
                payment_method=PaymentMethod.CARD,
                paid_at=datetime.now(),
                transaction_ref="TXN123456",
                notes="Paid via credit card"
            )
        ]
        db.add_all(payments)
        db.commit()

        print("Database seeded successfully!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()