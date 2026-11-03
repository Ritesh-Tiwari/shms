from datetime import date, time, timedelta
from decimal import Decimal

from django.core.exceptions import PermissionDenied
from django.test import TestCase, RequestFactory
from django.contrib.auth.models import AnonymousUser
from django.urls import reverse
from accounts.models import User
from accounts.choices import UserRole
from appointments.models import Appointment
from doctors.choices import SpecializationChoices
from doctors.models import Doctor
from patients.choices import BloodGroupChoices, GenderChoices
from patients.models import Patient
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


class GlobalSearchTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            username="search-patient",
            email="search-patient@example.com",
            password="StrongPassword123!",
            role=UserRole.PATIENT,
            first_name="Private",
            last_name="Patient",
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.OTHER,
            blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210",
            address="Test Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
        )
        self.other_patient_user = User.objects.create_user(
            username="other-search-patient",
            email="other-search-patient@example.com",
            password="StrongPassword123!",
            role=UserRole.PATIENT,
            first_name="Other",
            last_name="Patient",
        )
        self.other_patient = Patient.objects.create(
            user=self.other_patient_user,
            date_of_birth=date(1992, 2, 2),
            gender=GenderChoices.OTHER,
            blood_group=BloodGroupChoices.A_POSITIVE,
            emergency_contact="9876543211",
            address="Other Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700002",
        )
        self.doctor_user = User.objects.create_user(
            username="search-doctor",
            email="search-doctor@example.com",
            password="StrongPassword123!",
            role=UserRole.DOCTOR,
            first_name="Global",
            last_name="Doctor",
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=5,
            consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        self.other_doctor_user = User.objects.create_user(
            username="other-search-doctor",
            email="other-search-doctor@example.com",
            password="StrongPassword123!",
            role=UserRole.DOCTOR,
            first_name="Cross Scope",
            last_name="Doctor",
        )
        self.other_doctor = Doctor.objects.create(
            user=self.other_doctor_user,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=5,
            consultation_fee=Decimal("500.00"),
            address="Another Clinic Road",
        )
        self.own_appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today() + timedelta(days=1),
            appointment_time=time(10, 0),
            reason_for_visit="Routine check-up",
        )
        Appointment.objects.create(
            patient=self.other_patient,
            doctor=self.other_doctor,
            appointment_date=date.today() + timedelta(days=2),
            appointment_time=time(11, 0),
            reason_for_visit="Routine check-up",
        )

    def test_search_requires_authentication(self):
        response = self.client.get(reverse("core:search"), {"q": "Global"})
        self.assertRedirects(
            response,
            f"{reverse('accounts:login')}?next={reverse('core:search')}%3Fq%3DGlobal",
        )

    def test_blank_search_does_not_run_queries_and_uses_dashboard_as_safe_return(self):
        self.client.force_login(self.patient_user)

        with self.assertNumQueries(3):  # Includes the shared notification context query.
            response = self.client.get(reverse("core:search"), {"q": "   "})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], "")
        self.assertEqual(response.context["results"], [])
        self.assertEqual(
            response.context["return_url"],
            reverse("dashboard:dashboard"),
        )

    def test_search_back_link_accepts_local_return_path_only(self):
        self.client.force_login(self.patient_user)

        local_response = self.client.get(
            reverse("core:search"),
            {"q": "missing", "next": "/appointments/my/"},
        )
        external_response = self.client.get(
            reverse("core:search"),
            {"q": "missing", "next": "https://example.com/"},
        )

        self.assertEqual(local_response.context["return_url"], "/appointments/my/")
        self.assertEqual(
            external_response.context["return_url"],
            reverse("dashboard:dashboard"),
        )

    def test_patient_search_only_returns_their_own_records(self):
        self.client.force_login(self.patient_user)

        own_response = self.client.get(
            reverse("core:search"),
            {"q": "Global"},
        )
        private_response = self.client.get(
            reverse("core:search"),
            {"q": "Cross Scope"},
        )

        self.assertEqual(own_response.status_code, 200)
        self.assertEqual(len(own_response.context["results"]), 1)
        self.assertEqual(
            own_response.context["results"][0]["url"],
            reverse(
                "appointments:my-appointment-detail",
                args=[self.own_appointment.pk],
            ),
        )
        self.assertEqual(private_response.context["results"], [])

    def test_doctor_search_only_returns_their_own_appointments(self):
        self.client.force_login(self.doctor_user)

        response = self.client.get(
            reverse("core:search"),
            {"q": "Private"},
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["results"]), 1)
        self.assertEqual(
            response.context["results"][0]["url"],
            reverse("appointments:detail", args=[self.own_appointment.pk]),
        )