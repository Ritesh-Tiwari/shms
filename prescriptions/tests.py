from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase
from accounts.models import User
from accounts.choices import UserRole
from patients.models import Patient
from patients.choices import GenderChoices, BloodGroupChoices
from doctors.models import Doctor
from doctors.choices import SpecializationChoices
from appointments.models import Appointment, AppointmentStatus
from .models import Prescription, PrescriptionMedicine, PrescriptionStatus
from .forms import PrescriptionForm


class PrescriptionModelTests(TestCase):
    def setUp(self):
        patient_user = User.objects.create_user(
            username="rxpatient", email="rxpatient@example.com",
            password="StrongPassword123!", role=UserRole.PATIENT,
        )
        patient = Patient.objects.create(
            user=patient_user, date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE, blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210", address="Test Road",
            city="Kolkata", state="West Bengal", pincode="700001",
        )
        doctor_user = User.objects.create_user(
            username="rxdoctor", email="rxdoctor@example.com",
            password="StrongPassword123!", role=UserRole.DOCTOR,
        )
        doctor = Doctor.objects.create(
            user=doctor_user, specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS", experience=4, consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        self.appointment = Appointment.objects.create(
            patient=patient, doctor=doctor,
            appointment_date=date.today() - timedelta(days=1),
            appointment_time=time(10, 0), reason_for_visit="Fever",
            status=AppointmentStatus.COMPLETED,
        )

    def test_create_prescription_generates_id_and_defaults_active(self):
        prescription = Prescription.objects.create(
            appointment=self.appointment, diagnosis="Viral fever", remarks="Rest",
        )
        self.assertRegex(prescription.prescription_id, r"^PRE\d{6}$")
        self.assertEqual(prescription.status, PrescriptionStatus.ACTIVE)
        self.assertTrue(prescription.is_active)
        self.assertEqual(prescription.status_label, "Active")

    def test_prescription_medicine_is_related_to_prescription(self):
        prescription = Prescription.objects.create(
            appointment=self.appointment, diagnosis="Viral fever",
        )
        medicine = PrescriptionMedicine.objects.create(
            prescription=prescription, medicine_name="Paracetamol",
            dosage="500 mg", frequency="Twice daily", duration="3 days",
            instructions="After food",
        )
        self.assertEqual(prescription.medicines.count(), 1)
        self.assertEqual(str(medicine), "Paracetamol")

    def test_prescription_form_accepts_diagnosis_and_optional_remarks(self):
        form = PrescriptionForm(data={"diagnosis": "Migraine", "remarks": ""})
        self.assertTrue(form.is_valid())

    def test_appointment_can_have_only_one_prescription(self):
        Prescription.objects.create(appointment=self.appointment, diagnosis="First")
        with self.assertRaises(Exception):
            Prescription.objects.create(appointment=self.appointment, diagnosis="Duplicate")