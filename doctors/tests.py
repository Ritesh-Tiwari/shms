from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from accounts.choices import UserRole
from .choices import SpecializationChoices, AvailabilityChoices, Weekday
from .forms import DoctorScheduleForm
from .models import Doctor, DoctorSchedule
from .services import DoctorService


class DoctorServiceTests(TestCase):
    def user_data(self):
        return {
            "username": "doctortest",
            "email": "doctortest@example.com",
            "password": "StrongPassword123!",
            "first_name": "Asha",
            "last_name": "Sen",
            "phone_number": "9876543210",
        }

    def doctor_data(self):
        return {
            "specialization": SpecializationChoices.GENERAL_PHYSICIAN,
            "qualification": "MBBS",
            "experience": 5,
            "consultation_fee": Decimal("500.00"),
            "availability": AvailabilityChoices.AVAILABLE,
            "address": "Kolkata",
        }

    def test_create_doctor_creates_user_and_profile(self):
        doctor = DoctorService.create_doctor(self.user_data(), self.doctor_data())
        self.assertTrue(doctor.doctor_id.startswith("DOC"))
        self.assertEqual(doctor.user.role, UserRole.DOCTOR)
        self.assertTrue(doctor.user.check_password("StrongPassword123!"))

    def test_doctor_badge_properties(self):
        doctor = DoctorService.create_doctor(self.user_data(), self.doctor_data())
        self.assertEqual(doctor.badge_bg_class, "bg-slate-100 text-slate-800")
        self.assertEqual(doctor.status_icon, "check_circle")

    def test_schedule_form_rejects_end_time_before_start_time(self):
        form = DoctorScheduleForm(data={
            "weekday": Weekday.MONDAY,
            "start_time": "11:00",
            "end_time": "10:00",
            "is_active": True,
        })
        self.assertFalse(form.is_valid())
        self.assertIn("end_time", form.errors)

    def test_doctor_list_rejects_patient_role(self):
        patient = User.objects.create_user(
            username="doctorlistpatient",
            email="doctorlistpatient@example.com",
            password="StrongPassword123!",
            role=UserRole.PATIENT,
        )
        self.client.force_login(patient)
        response = self.client.get(reverse("doctors:list"))
        self.assertEqual(response.status_code, 403)