from django.test import TestCase

from django.urls import reverse

from accounts.choices import UserRole
from accounts.models import User

from .models import AuditLog
from .services import log_security_event


class AuditLogWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="audit-admin",
            email="audit-admin@example.com",
            password="StrongPassword123!",
            role=UserRole.ADMIN,
        )
        self.patient = User.objects.create_user(
            username="audit-patient",
            email="audit-patient@example.com",
            password="StrongPassword123!",
            role=UserRole.PATIENT,
        )

    def test_authentication_and_logout_events_are_recorded(self):
        login_url = reverse("accounts:login")
        failed_response = self.client.post(
            login_url,
            {"username": self.patient.email, "password": "WrongPassword!"},
        )
        self.assertEqual(failed_response.status_code, 200)

        success_response = self.client.post(
            login_url,
            {"username": self.patient.email, "password": "StrongPassword123!"},
        )
        self.assertEqual(success_response.status_code, 302)

        logout_response = self.client.post(reverse("accounts:logout"))
        self.assertEqual(logout_response.status_code, 302)

        self.assertTrue(
            AuditLog.objects.filter(
                action="LOGIN_FAILURE",
                outcome=AuditLog.Outcome.FAILURE,
                target_identifier=self.patient.email,
                actor__isnull=True,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="LOGIN",
                outcome=AuditLog.Outcome.SUCCESS,
                actor=self.patient,
                target_user=self.patient,
            ).exists()
        )
        self.assertTrue(
            AuditLog.objects.filter(
                action="LOGOUT",
                outcome=AuditLog.Outcome.SUCCESS,
                actor=self.patient,
            ).exists()
        )

    def test_denied_role_access_is_recorded_and_only_admin_can_view_logs(self):
        self.client.force_login(self.patient)
        response = self.client.get(reverse("dashboard:security-audit"))

        self.assertEqual(response.status_code, 403)
        denied_event = AuditLog.objects.get(action="ACCESS_DENIED")
        self.assertEqual(denied_event.actor, self.patient)
        self.assertEqual(denied_event.outcome, AuditLog.Outcome.DENIED)
        self.assertEqual(denied_event.details, {"view": "audit_log_list"})

        self.client.force_login(self.admin)
        response = self.client.get(reverse("dashboard:security-audit"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ACCESS_DENIED")

    def test_audit_log_filters_by_outcome_and_action(self):
        log_security_event(
            None,
            action="LOGIN_FAILURE",
            outcome=AuditLog.Outcome.FAILURE,
            target_identifier="unknown@example.com",
        )
        log_security_event(
            None,
            action="ACCOUNT_DEACTIVATED",
            outcome=AuditLog.Outcome.SUCCESS,
            target_identifier="patient@example.com",
        )
        self.client.force_login(self.admin)

        response = self.client.get(
            reverse("dashboard:security-audit"),
            {"action": "LOGIN_FAILURE", "outcome": AuditLog.Outcome.FAILURE},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["page_obj"].paginator.count, 1)
        self.assertContains(response, "unknown@example.com")
        self.assertNotContains(response, "patient@example.com")

    def test_account_status_changes_record_success_and_denial(self):
        self.client.force_login(self.admin)
        response = self.client.post(
            reverse("dashboard:toggle-status", args=[self.patient.pk])
        )
        self.assertEqual(response.status_code, 302)

        activated = AuditLog.objects.get(action="ACCOUNT_DEACTIVATED")
        self.assertEqual(activated.actor, self.admin)
        self.assertEqual(activated.target_user, self.patient)
        self.assertEqual(activated.outcome, AuditLog.Outcome.SUCCESS)

        response = self.client.post(
            reverse("dashboard:toggle-status", args=[self.admin.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertTrue(
            AuditLog.objects.filter(
                action="ACCOUNT_STATUS_CHANGE",
                outcome=AuditLog.Outcome.DENIED,
                actor=self.admin,
                target_user=self.admin,
            ).exists()
        )

    def test_target_identifier_is_bounded_to_model_field_length(self):
        event = log_security_event(
            None,
            action="LOGIN_FAILURE",
            outcome=AuditLog.Outcome.FAILURE,
            target_identifier="a" * 300,
        )

        self.assertEqual(len(event.target_identifier), 254)
