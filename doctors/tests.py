from decimal import Decimal
from datetime import date, time, timedelta
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from accounts.choices import UserRole
from appointments.services import AppointmentService
from patients.choices import BloodGroupChoices, GenderChoices
from patients.models import Patient
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

    def test_doctor_registration_action_is_admin_only(self):
        doctor = DoctorService.create_doctor(self.user_data(), self.doctor_data())
        users = {
            UserRole.ADMIN: User.objects.create_user(
                username="doctorlistadmin",
                email="doctorlistadmin@example.com",
                password="StrongPassword123!",
                role=UserRole.ADMIN,
            ),
            UserRole.DOCTOR: doctor.user,
            UserRole.RECEPTIONIST: User.objects.create_user(
                username="doctorlistreceptionist",
                email="doctorlistreceptionist@example.com",
                password="StrongPassword123!",
                role=UserRole.RECEPTIONIST,
            ),
            UserRole.PATIENT: User.objects.create_user(
                username="doctorlistpatientaction",
                email="doctorlistpatientaction@example.com",
                password="StrongPassword123!",
                role=UserRole.PATIENT,
            ),
        }

        for role, user in users.items():
            with self.subTest(role=role):
                self.client.force_login(user)
                response = self.client.get(reverse("doctors:list"))
                if role in (UserRole.ADMIN, UserRole.RECEPTIONIST):
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(
                        reverse("doctors:register") in response.content.decode(),
                        role == UserRole.ADMIN,
                    )
                else:
                    self.assertEqual(response.status_code, 403)


class PatientClinicalSummaryTests(TestCase):
    def setUp(self):
        doctor_user = User.objects.create_user(
            username="summarydoctor",
            email="summarydoctor@example.com",
            password="StrongPassword123!",
            role=UserRole.DOCTOR,
        )
        self.doctor = Doctor.objects.create(
            user=doctor_user,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=5,
            consultation_fee=Decimal("500.00"),
            address="Kolkata",
        )
        patient_user = User.objects.create_user(
            username="summarypatient",
            email="summarypatient@example.com",
            password="StrongPassword123!",
            role=UserRole.PATIENT,
        )
        self.patient = Patient.objects.create(
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

    def test_summary_loads_when_patient_has_multiple_appointments(self):
        appointment_date = date.today() + timedelta(days=2)
        for appointment_time in (time(10, 0), time(11, 0)):
            AppointmentService.create_appointment(
                {
                    "patient": self.patient,
                    "doctor": self.doctor,
                    "appointment_date": appointment_date,
                    "appointment_time": appointment_time,
                    "reason_for_visit": "Routine check-up",
                }
            )

        self.client.force_login(self.doctor.user)
        response = self.client.get(
            reverse("doctors:patient-summary", args=[self.patient.pk])
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["appointments"].count(), 2)

    def test_weekly_schedule_is_only_available_to_doctors(self):
        users = {
            UserRole.ADMIN: User.objects.create_user(
                username="scheduleadmin",
                email="scheduleadmin@example.com",
                password="StrongPassword123!",
                role=UserRole.ADMIN,
            ),
            UserRole.DOCTOR: self.doctor.user,
            UserRole.RECEPTIONIST: User.objects.create_user(
                username="schedulereceptionist",
                email="schedulereceptionist@example.com",
                password="StrongPassword123!",
                role=UserRole.RECEPTIONIST,
            ),
            UserRole.PATIENT: self.patient.user,
        }

        for role, user in users.items():
            with self.subTest(role=role):
                self.client.force_login(user)
                response = self.client.get(reverse("doctors:schedule"))
                self.assertEqual(
                    response.status_code,
                    200 if role == UserRole.DOCTOR else 403,
                )