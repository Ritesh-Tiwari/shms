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
from .models import Appointment, AppointmentStatus
from .services import AppointmentService


class AppointmentServiceTests(TestCase):
    def setUp(self):
        patient_user = User.objects.create_user(
            username="apptpatient", email="apptpatient@example.com",
            password="StrongPassword123!", role=UserRole.PATIENT,
        )
        self.patient = Patient.objects.create(
            user=patient_user, date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE, blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210", address="Test Road",
            city="Kolkata", state="West Bengal", pincode="700001",
        )
        doctor_user = User.objects.create_user(
            username="apptdoctor", email="apptdoctor@example.com",
            password="StrongPassword123!", role=UserRole.DOCTOR,
        )
        self.doctor = Doctor.objects.create(
            user=doctor_user, specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS", experience=4, consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )

    def create_appointment(self, **overrides):
        data = {
            "patient": self.patient,
            "doctor": self.doctor,
            "appointment_date": date.today() + timedelta(days=2),
            "appointment_time": time(10, 0),
            "reason_for_visit": "Routine check-up",
        }
        data.update(overrides)
        return AppointmentService.create_appointment(data)

    def test_create_appointment_generates_identifier(self):
        appointment = self.create_appointment()
        self.assertRegex(appointment.appointment_id, r"^APT\d{6}$")
        self.assertEqual(appointment.status, AppointmentStatus.SCHEDULED)

    def test_cancel_appointment_changes_status(self):
        appointment = self.create_appointment()
        AppointmentService.cancel_appointment(appointment)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, AppointmentStatus.CANCELLED)

    def test_cannot_cancel_completed_appointment(self):
        appointment = self.create_appointment(status=AppointmentStatus.COMPLETED)
        with self.assertRaises(ValueError):
            AppointmentService.cancel_appointment(appointment)

    def test_status_transition_scheduled_to_confirmed(self):
        appointment = self.create_appointment()
        AppointmentService.update_status(appointment, AppointmentStatus.CONFIRMED)
        appointment.refresh_from_db()
        self.assertEqual(appointment.status, AppointmentStatus.CONFIRMED)

    def test_invalid_status_transition_raises_value_error(self):
        appointment = self.create_appointment(status=AppointmentStatus.CANCELLED)
        with self.assertRaises(ValueError):
            AppointmentService.update_status(appointment, AppointmentStatus.COMPLETED)

    def test_appointment_search_works_with_all_status_filter(self):
        appointment = self.create_appointment()
        admin = User.objects.create_user(
            username="apptadmin",
            email="apptadmin@example.com",
            password="StrongPassword123!",
            role=UserRole.ADMIN,
        )
        self.client.force_login(admin)

        response = self.client.get(
            reverse("appointments:list"),
            {"search": appointment.appointment_id, "status": "all"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertEqual(
            response.context["page_obj"].object_list[0],
            appointment,
        )