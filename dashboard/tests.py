from datetime import date, time, timedelta
from decimal import Decimal

from django.test import RequestFactory, TestCase
from django.urls import reverse
from django.utils import timezone
from accounts.models import User
from accounts.choices import UserRole
from appointments.models import Appointment, AppointmentStatus
from billing.models import Billing, Payment, PaymentMethod, PaymentType
from core.context_processors import recent_activities
from core.models import Notification
from core.notification_services import (
    notify_appointment_event,
    notify_patient_registered,
    notify_payment_created,
)
from doctors.choices import SpecializationChoices
from doctors.models import Doctor
from patients.choices import BloodGroupChoices, GenderChoices
from patients.models import Patient


class AdminAccountManagementTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="admin-dashboard",
            email="admin-dashboard@example.com",
            password="StrongPassword123!",
            role=UserRole.ADMIN,
        )
        self.patient = User.objects.create_user(
            username="dashboard-patient",
            email="dashboard-patient@example.com",
            password="StrongPassword123!",
            role=UserRole.PATIENT,
        )
        self.doctor = User.objects.create_user(
            username="dashboard-doctor",
            email="dashboard-doctor@example.com",
            password="StrongPassword123!",
            role=UserRole.DOCTOR,
            is_active=False,
        )

    def test_admin_can_open_account_list(self):
        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:accounts"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["total_accounts"], 2)

    def test_dashboard_appointment_row_links_to_appointment_detail(self):
        patient = Patient.objects.create(
            user=self.patient,
            date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE,
            blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210",
            address="Test Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
        )
        doctor = Doctor.objects.create(
            user=self.doctor,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=4,
            consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=timezone.localdate(),
            appointment_time=time(10, 0),
            reason_for_visit="Check-up",
        )
        detail_url = reverse("appointments:detail", args=[appointment.pk])
        self.client.force_login(self.admin)

        response = self.client.get(reverse("dashboard:dashboard"))

        self.assertContains(response, f'data-href="{detail_url}"')
        self.assertContains(response, 'role="link"')
        self.assertEqual(self.client.get(detail_url).status_code, 200)

    def test_notification_menu_shows_recent_activities_and_unread_count(self):
        patient_profile = Patient.objects.create(
            user=self.patient,
            date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE,
            blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210",
            address="Test Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
        )
        notify_patient_registered(patient_profile, actor=self.admin)
        doctor_profile = Doctor.objects.create(
            user=self.doctor,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=4,
            consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        appointment = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason_for_visit="Check-up",
            status=AppointmentStatus.SCHEDULED,
        )
        notify_appointment_event(
            appointment,
            actor=self.patient,
            event="booked",
        )
        billing = Billing.objects.create(
            appointment=appointment,
            patient=patient_profile,
            amount=Decimal("500.00"),
            tax_amount=Decimal("0.00"),
            total_amount=Decimal("500.00"),
        )
        payment = Payment.objects.create(
            billing=billing,
            amount=Decimal("500.00"),
            payment_method=PaymentMethod.CASH,
            payment_type=PaymentType.ADVANCE,
        )
        notify_payment_created(payment, actor=self.admin)

        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:accounts"))

        self.assertContains(response, 'id="notification-button"')
        self.assertContains(response, "3 unread")
        self.assertContains(
            response,
            "New patient dashboard-patient registered.",
        )
        self.assertContains(
            response,
            "Payment of ₹500.00 received from dashboard-patient.",
        )
        self.assertContains(
            response,
            "Appointment booked for dashboard-patient with Dr. dashboard-doctor.",
        )

        dashboard_response = self.client.get(reverse("dashboard:dashboard"))
        self.assertContains(dashboard_response, "Recent Activities")
        self.assertContains(
            dashboard_response,
            "New patient dashboard-patient registered.",
        )
        self.assertContains(dashboard_response, 'action="/notifications/')

    def test_non_admin_does_not_receive_admin_activity_notifications(self):
        request = RequestFactory().get("/")
        request.user = self.patient

        self.assertEqual(
            recent_activities(request)["recent_activities"],
            [],
        )

    def test_recent_activities_are_limited_to_ten(self):
        for index in range(11):
            Notification.objects.create(
                recipient=self.admin,
                message=f"Activity {index}",
                target_url=reverse("dashboard:dashboard"),
            )

        request = RequestFactory().get("/")
        request.user = self.admin
        self.assertEqual(
            len(recent_activities(request)["recent_activities"]),
            10,
        )

    def test_notifications_are_visible_only_to_their_recipient(self):
        notification = Notification.objects.create(
            recipient=self.admin,
            message="Private activity",
            target_url=reverse("dashboard:dashboard"),
        )
        self.client.force_login(self.patient)

        response = self.client.post(
            reverse("core:notification-open", args=[notification.pk])
        )

        self.assertEqual(response.status_code, 404)
        notification.refresh_from_db()
        self.assertIsNone(notification.read_at)

    def test_patient_gets_header_notifications_without_an_activity_card(self):
        Notification.objects.create(
            recipient=self.patient,
            message="Your appointment request was booked.",
            target_url=reverse("appointments:my-appointments"),
        )
        self.client.force_login(self.patient)

        response = self.client.get(reverse("core:search"), {"q": "missing"})

        self.assertContains(response, 'id="notification-button"')
        self.assertContains(response, "Your appointment request was booked.")
        self.assertNotContains(response, "Recent Activities")

    def test_opening_notification_marks_only_owned_notification_read(self):
        notification = Notification.objects.create(
            recipient=self.admin,
            message="Private activity",
            target_url=reverse("dashboard:dashboard"),
        )
        self.client.force_login(self.admin)

        response = self.client.post(
            reverse("core:notifications-mark-read"),
            {"notification_ids": [str(notification.pk)]},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["unread_count"], 0)
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

    def test_cancellation_notifications_are_role_scoped_and_name_actor(self):
        patient_profile = Patient.objects.create(
            user=self.patient,
            date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE,
            blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210",
            address="Test Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
        )
        doctor_profile = Doctor.objects.create(
            user=self.doctor,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=4,
            consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        receptionist = User.objects.create_user(
            username="dashboard-receptionist",
            email="dashboard-receptionist@example.com",
            password="TestPassword123!",
            role=UserRole.RECEPTIONIST,
        )
        appointment = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason_for_visit="Check-up",
            status=AppointmentStatus.CANCELLED,
        )
        notify_appointment_event(
            appointment,
            actor=self.doctor,
            event="cancelled",
        )

        patient_notification = Notification.objects.get(recipient=self.patient)
        doctor_notification = Notification.objects.get(recipient=self.doctor)
        receptionist_notification = Notification.objects.get(
            recipient=receptionist
        )

        self.assertIn("cancelled by dashboard-doctor", patient_notification.message)
        self.assertEqual(
            patient_notification.target_url,
            reverse("appointments:my-appointment-detail", args=[appointment.pk]),
        )
        self.assertEqual(
            doctor_notification.target_url,
            reverse("appointments:detail", args=[appointment.pk]),
        )
        self.assertIn("cancelled by dashboard-doctor", receptionist_notification.message)

    def test_patient_booking_notification_links_to_patient_appointment_detail(self):
        patient_profile = Patient.objects.create(
            user=self.patient,
            date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE,
            blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210",
            address="Test Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
        )
        doctor_profile = Doctor.objects.create(
            user=self.doctor,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=4,
            consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        appointment = Appointment.objects.create(
            patient=patient_profile,
            doctor=doctor_profile,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason_for_visit="Check-up",
            status=AppointmentStatus.SCHEDULED,
        )
        notify_appointment_event(
            appointment,
            actor=self.patient,
            event="booked",
        )
        notification = Notification.objects.get(
            recipient=self.patient,
            message__contains="appointment request",
        )

        self.client.force_login(self.patient)
        response = self.client.post(
            reverse("core:notification-open", args=[notification.pk])
        )

        self.assertRedirects(
            response,
            reverse("appointments:my-appointment-detail", args=[appointment.pk]),
        )
        notification.refresh_from_db()
        self.assertIsNotNone(notification.read_at)

    def test_account_list_can_filter_by_role(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("dashboard:accounts"), {"role": UserRole.PATIENT}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_account_list_can_filter_active_status(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("dashboard:accounts"), {"status": "inactive"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_non_admin_cannot_open_account_list(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse("dashboard:accounts"))
        self.assertEqual(response.status_code, 403)

    def test_toggle_status_requires_post(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("dashboard:toggle-status", args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 405)

    def test_admin_can_deactivate_managed_account(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("dashboard:toggle-status", args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.patient.refresh_from_db()
        self.assertFalse(self.patient.is_active)

    def test_admin_cannot_toggle_own_account(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("dashboard:toggle-status", args=[self.admin.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.admin.refresh_from_db()
        self.assertTrue(self.admin.is_active)

    def test_admin_account_list_searches_by_email(self):
        self.client.force_login(self.admin)
        response = self.client.get(
            reverse("dashboard:accounts"), {"q": "dashboard-patient@example.com"}
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)