from urllib.parse import urlsplit

from django.core import mail
from django.test import TestCase
from django.test import override_settings
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


@override_settings(EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend")
class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="resetuser",
            email="reset@example.com",
            password="OriginalPassword123!",
            role=UserRole.PATIENT,
        )

    def test_reset_email_link_changes_password(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": self.user.email},
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_done"),
        )
        self.assertEqual(len(mail.outbox), 1)
        self.assertEqual(mail.outbox[0].to, [self.user.email])

        reset_url = next(
            line
            for line in mail.outbox[0].body.splitlines()
            if "/accounts/reset/" in line
        )
        reset_path = urlsplit(reset_url).path

        response = self.client.get(reset_path)
        self.assertEqual(response.status_code, 302)
        confirm_path = response["Location"]

        response = self.client.post(
            confirm_path,
            {
                "new_password1": "NewStrongPassword123!",
                "new_password2": "NewStrongPassword123!",
            },
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_complete"),
        )
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("NewStrongPassword123!"))

    def test_unknown_email_does_not_send_a_reset_email(self):
        response = self.client.post(
            reverse("accounts:password_reset"),
            {"email": "unknown@example.com"},
        )

        self.assertRedirects(
            response,
            reverse("accounts:password_reset_done"),
        )
        self.assertEqual(len(mail.outbox), 0)