from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from accounts.choices import UserRole
from patients.models import Patient
from patients.choices import GenderChoices, BloodGroupChoices
from doctors.models import Doctor, DoctorSchedule
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

    def test_appointment_detail_actions_and_update_access_match_roles(self):
        appointment = self.create_appointment()
        admin = User.objects.create_user(
            username="apptdetailadmin",
            email="apptdetailadmin@example.com",
            password="StrongPassword123!",
            role=UserRole.ADMIN,
        )
        receptionist = User.objects.create_user(
            username="apptdetailreceptionist",
            email="apptdetailreceptionist@example.com",
            password="StrongPassword123!",
            role=UserRole.RECEPTIONIST,
        )
        detail_url = reverse("appointments:detail", args=[appointment.pk])
        update_url = reverse("appointments:update", args=[appointment.pk])

        for role, user in (
            (UserRole.ADMIN, admin),
            (UserRole.DOCTOR, self.doctor.user),
            (UserRole.RECEPTIONIST, receptionist),
        ):
            with self.subTest(role=role):
                self.client.force_login(user)
                response = self.client.get(detail_url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(
                    update_url in response.content.decode(),
                    role in (UserRole.ADMIN, UserRole.RECEPTIONIST),
                )
                if role == UserRole.DOCTOR:
                    self.assertIn(
                        reverse(
                            "doctors:patient-summary",
                            args=[self.patient.pk],
                        ),
                        response.content.decode(),
                    )
                    self.assertIn(
                        reverse("doctors:dashboard"),
                        response.content.decode(),
                    )
                else:
                    self.assertIn(
                        reverse("patients:detail", args=[self.patient.pk]),
                        response.content.decode(),
                    )
                    self.assertIn(
                        reverse(
                            "doctors:detail",
                            args=[self.doctor.pk],
                        ),
                        response.content.decode(),
                    )
                self.assertEqual(
                    self.client.get(update_url).status_code,
                    200 if role in (UserRole.ADMIN, UserRole.RECEPTIONIST) else 403,
                )

        self.client.force_login(self.patient.user)
        self.assertEqual(self.client.get(detail_url).status_code, 403)
        self.assertEqual(
            self.client.get(
                reverse(
                    "appointments:my-appointment-detail",
                    args=[appointment.pk],
                )
            ).status_code,
            200,
        )

    def test_update_page_loads_available_slots_including_current_appointment(self):
        appointment_date = date.today() + timedelta(days=2)
        appointment = self.create_appointment(
            appointment_date=appointment_date,
            appointment_time=time(10, 0),
        )
        DoctorSchedule.objects.create(
            doctor=self.doctor,
            weekday=appointment_date.weekday(),
            start_time=time(10, 0),
            end_time=time(10, 30),
        )
        admin = User.objects.create_user(
            username="apptavailabilityadmin",
            email="apptavailabilityadmin@example.com",
            role=UserRole.ADMIN,
        )
        self.client.force_login(admin)

        update_response = self.client.get(
            reverse("appointments:update", args=[appointment.pk])
        )
        self.assertContains(update_response, "data-availability-form")
        self.assertContains(
            update_response,
            f'data-doctor-id="{self.doctor.pk}"',
        )
        self.assertContains(
            update_response,
            f'data-exclude-appointment-id="{appointment.pk}"',
        )
        self.assertContains(
            update_response,
            f'data-selected-date="{appointment_date.isoformat()}"',
        )
        self.assertContains(
            update_response,
            'data-selected-time="10:00"',
        )

        dates_response = self.client.get(
            reverse("appointments:available-dates"),
            {
                "doctor_id": self.doctor.pk,
                "exclude_appointment_id": appointment.pk,
            },
        )
        self.assertEqual(dates_response.status_code, 200)
        self.assertIn(
            appointment_date.isoformat(),
            [item["value"] for item in dates_response.json()["dates"]],
        )

        times_response = self.client.get(
            reverse("appointments:available-times"),
            {
                "doctor_id": self.doctor.pk,
                "date": appointment_date.isoformat(),
                "exclude_appointment_id": appointment.pk,
            },
        )
        self.assertEqual(times_response.status_code, 200)
        self.assertEqual(
            [item["value"] for item in times_response.json()["times"]],
            ["10:00"],
        )

        update_response = self.client.post(
            reverse("appointments:update", args=[appointment.pk]),
            {
                "appointment_date": appointment_date.isoformat(),
                "appointment_time": "10:00",
                "reason_for_visit": appointment.reason_for_visit,
            },
        )
        self.assertRedirects(
            update_response,
            reverse("appointments:detail", args=[appointment.pk]),
        )