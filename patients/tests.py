from datetime import date
from django.test import TestCase
from django.urls import reverse
from accounts.models import User
from accounts.choices import UserRole
from .choices import GenderChoices, BloodGroupChoices
from .models import Patient
from .services import PatientService


class PatientServiceTests(TestCase):
    def patient_data(self):
        return {
            "date_of_birth": date(1995, 5, 12),
            "gender": GenderChoices.MALE,
            "blood_group": BloodGroupChoices.O_POSITIVE,
            "emergency_contact": "9876543210",
            "address": "12 Test Road",
            "city": "Kolkata",
            "state": "West Bengal",
            "pincode": "700001",
            "allergies": "None",
            "medical_history": "None",
        }

    def test_create_patient_creates_user_and_patient_profile(self):
        patient = PatientService.create_patient(
            user_data={
                "username": "patienttest",
                "email": "patienttest@example.com",
                "first_name": "Test",
                "last_name": "Patient",
                "password": "StrongPassword123!",
            },
            patient_data=self.patient_data(),
        )
        self.assertIsNotNone(patient.pk)
        self.assertEqual(patient.user.role, UserRole.PATIENT)
        self.assertTrue(patient.patient_id.startswith("PAT"))
        self.assertTrue(patient.user.check_password("StrongPassword123!"))

    def test_patient_age_property(self):
        patient = Patient.objects.create(
            user=User.objects.create_user(
                username="agepatient",
                email="agepatient@example.com",
                password="StrongPassword123!",
                role=UserRole.PATIENT,
            ),
            **self.patient_data(),
        )
        expected_age = date.today().year - date(1995, 5, 12).year
        if (date.today().month, date.today().day) < (5, 12):
            expected_age -= 1
        self.assertEqual(patient.age, expected_age)

    def test_patient_identifier_is_generated(self):
        patient = Patient.objects.create(
            user=User.objects.create_user(
                username="idpatient",
                email="idpatient@example.com",
                password="StrongPassword123!",
                role=UserRole.PATIENT,
            ),
            **self.patient_data(),
        )
        self.assertRegex(patient.patient_id, r"^PAT\d{6}$")

    def test_patient_home_requires_patient_role(self):
        admin = User.objects.create_user(
            username="patienttestadmin",
            email="patienttestadmin@example.com",
            password="StrongPassword123!",
            role=UserRole.ADMIN,
        )
        self.client.force_login(admin)
        response = self.client.get(reverse("patients:home"))
        self.assertEqual(response.status_code, 403)