from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from accounts.choices import UserRole


class UserModelTests(TestCase):
    def test_create_user_hashes_password_and_uses_email(self):
        user = User.objects.create_user(
            username="testpatient",
            email="patient-test@example.com",
            password="StrongPassword123!",
            role=UserRole.PATIENT,
        )
        self.assertEqual(user.email, "patient-test@example.com")
        self.assertTrue(user.check_password("StrongPassword123!"))
        self.assertNotEqual(user.password, "StrongPassword123!")

    def test_email_must_be_unique(self):
        User.objects.create_user(
            username="firstuser",
            email="duplicate@example.com",
            password="StrongPassword123!",
        )
        with self.assertRaises(Exception):
            User.objects.create_user(
                username="seconduser",
                email="duplicate@example.com",
                password="StrongPassword123!",
            )


class AuthenticationViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="loginuser",
            email="login@example.com",
            password="StrongPassword123!",
            role=UserRole.PATIENT,
        )

    def test_login_page_loads(self):
        response = self.client.get(reverse("accounts:login"))
        self.assertEqual(response.status_code, 200)

    def test_valid_login_redirects_to_dashboard(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.email, "password": "StrongPassword123!"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("dashboard:dashboard"))

    def test_invalid_login_shows_login_page(self):
        response = self.client.post(
            reverse("accounts:login"),
            {"username": self.user.email, "password": "WrongPassword!"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_requires_post_and_logs_user_out(self):
        self.client.force_login(self.user)
        response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse("accounts:login"))
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout_rejects_get(self):
        self.client.force_login(self.user)
        response = self.client.get(reverse("accounts:logout"))
        self.assertEqual(response.status_code, 405)