from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
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


class PrescriptionPdfAccessTests(TestCase):
    def setUp(self):
        patient_user = User.objects.create_user(
            username="rx-access-patient",
            email="rx-access-patient@example.com",
            password="test-password-123",
            role=UserRole.PATIENT,
        )
        patient = Patient.objects.create(
            user=patient_user,
            date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE,
            blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210",
            address="Test Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
        )
        doctor_user = User.objects.create_user(
            username="rx-access-doctor",
            email="rx-access-doctor@example.com",
            password="test-password-123",
            role=UserRole.DOCTOR,
        )
        doctor = Doctor.objects.create(
            user=doctor_user,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=4,
            consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=date.today() - timedelta(days=1),
            appointment_time=time(10, 0),
            reason_for_visit="Check-up",
            status=AppointmentStatus.COMPLETED,
        )
        self.prescription = Prescription.objects.create(
            appointment=appointment,
            diagnosis="Seasonal allergies",
        )
        self.receptionist = User.objects.create_user(
            username="rx-access-receptionist",
            email="rx-access-receptionist@example.com",
            password="test-password-123",
            role=UserRole.RECEPTIONIST,
        )

    def test_receptionist_can_view_and_download_prescription_pdf(self):
        self.client.force_login(self.receptionist)

        detail_response = self.client.get(
            reverse("prescriptions:detail", args=[self.prescription.pk])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Download PDF")

        pdf_response = self.client.get(
            reverse("prescriptions:pdf", args=[self.prescription.pk])
        )
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))

    def test_patient_and_doctor_can_download_only_their_prescriptions(self):
        appointment = self.prescription.appointment
        other_patient = User.objects.create_user(
            username="rx-other-patient",
            email="rx-other-patient@example.com",
            password="testpass123",
            role=UserRole.PATIENT,
        )
        other_doctor = User.objects.create_user(
            username="rx-other-doctor",
            email="rx-other-doctor@example.com",
            password="testpass123",
            role=UserRole.DOCTOR,
        )
        pdf_url = reverse("prescriptions:pdf", args=[self.prescription.pk])

        for user, expected_status in (
            (appointment.patient.user, 200),
            (other_patient, 403),
            (appointment.doctor.user, 200),
            (other_doctor, 403),
        ):
            with self.subTest(user=user.username):
                self.client.force_login(user)
                response = self.client.get(pdf_url)
                self.assertEqual(response.status_code, expected_status)