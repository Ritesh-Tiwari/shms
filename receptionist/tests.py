from datetime import date

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from accounts.choices import UserRole

from .models import Receptionist
from .services import ReceptionistService


class ReceptionistServiceTests(TestCase):

    def setUp(self):

        self.admin = User.objects.create_user(
            username="admin01",
            email="admin@example.com",
            password="StrongAdminPassword123!",
            role=UserRole.ADMIN,
        )

    def test_create_receptionist(self):

        receptionist = (
            ReceptionistService.create_receptionist(

                user_data={
                    "username": "reception01",
                    "email": "reception01@example.com",
                    "password": "StrongReceptionPassword123!",
                    "first_name": "Amit",
                    "last_name": "Kumar",
                    "phone_number": "9876543210",
                },

                profile_data={
                    "joining_date": date(2026, 10, 14),
                },
            )
        )

        self.assertIsNotNone(
            receptionist.pk
        )

        self.assertTrue(
            receptionist.receptionist_id.startswith("REC")
        )

        self.assertEqual(
            receptionist.user.role,
            UserRole.RECEPTIONIST,
        )

        self.assertTrue(
            receptionist.user.check_password(
                "StrongReceptionPassword123!"
            )
        )

    def test_admin_can_create_receptionist_from_form(self):

        self.client.force_login(
            self.admin
        )

        response = self.client.post(
            reverse("receptionist:create"),
            {
                "username": "formreception01",
                "first_name": "Riya",
                "last_name": "Sharma",
                "email": "formreception01@example.com",
                "phone_number": "9876543211",
                "password": "FormReceptionPassword123!",
                "joining_date": "2026-10-15",
            },
        )

        self.assertEqual(
            response.status_code,
            302,
        )

        receptionist = Receptionist.objects.get(
            user__username="formreception01",
        )

        self.assertTrue(
            receptionist.receptionist_id.startswith("REC")
        )
        self.assertEqual(
            receptionist.user.role,
            UserRole.RECEPTIONIST,
        )

    def test_receptionist_profile_has_unique_user(self):

        user = User.objects.create_user(
            username="reception02",
            email="reception02@example.com",
            password="StrongReceptionPassword123!",
            role=UserRole.RECEPTIONIST,
        )

        Receptionist.objects.create(
            user=user,
            joining_date=date(2026, 10, 14),
        )

        with self.assertRaises(Exception):

            Receptionist.objects.create(
                user=user,
                joining_date=date(2026, 10, 15),
            )

    def test_admin_can_open_receptionist_list(self):

        self.client.force_login(
            self.admin
        )

        response = self.client.get(
            reverse("receptionist:list")
        )

        self.assertEqual(
            response.status_code,
            200,
        )

    def test_patient_cannot_open_receptionist_list(self):

        patient = User.objects.create_user(
            username="patient01",
            email="patient@example.com",
            password="StrongPatientPassword123!",
            role=UserRole.PATIENT,
        )

        self.client.force_login(
            patient
        )

        response = self.client.get(
            reverse("receptionist:list")
        )

        self.assertEqual(
            response.status_code,
            403,
        )

