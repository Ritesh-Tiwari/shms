from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from accounts.models import User
from accounts.choices import UserRole
from .decorators import role_required


class RoleRequiredDecoratorTests(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.admin = User.objects.create_user(
            username="core-admin", email="core-admin@example.com",
            password="StrongPassword123!", role=UserRole.ADMIN,
        )
        self.patient = User.objects.create_user(
            username="core-patient", email="core-patient@example.com",
            password="StrongPassword123!", role=UserRole.PATIENT,
        )

    def test_allowed_role_can_call_view(self):
        @role_required(UserRole.ADMIN)
        def sample_view(request):
            from django.http import HttpResponse
            return HttpResponse("ok")

        request = self.factory.get("/")
        request.user = self.admin
        response = sample_view(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, b"ok")

    def test_disallowed_role_raises_permission_denied(self):
        @role_required(UserRole.ADMIN)
        def sample_view(request):
            from django.http import HttpResponse
            return HttpResponse("ok")

        request = self.factory.get("/")
        request.user = self.patient
        with self.assertRaises(PermissionDenied):
            sample_view(request)

    def test_anonymous_user_is_redirected_to_login(self):
        @role_required(UserRole.ADMIN)
        def sample_view(request):
            from django.http import HttpResponse
            return HttpResponse("ok")

        request = self.factory.get("/")
        request.user = AnonymousUser()
        response = sample_view(request)
        self.assertEqual(response.status_code, 302)