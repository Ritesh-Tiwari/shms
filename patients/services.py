from django.db import transaction

from accounts.models import User
from .models import Patient


class PatientService:

    @staticmethod
    @transaction.atomic
    def create_patient(*, user_data, patient_data,):
        """
        Create a User and Patient in a single transaction.
        """

        user = User.objects.create_user(
            username=user_data["email"],
            email=user_data["email"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            password=user_data["password"],
            role="PATIENT",
        )

        patient = Patient.objects.create(
            user=user,
            **patient_data,
        )

        return patient