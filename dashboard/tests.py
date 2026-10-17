from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from accounts.choices import UserRole


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