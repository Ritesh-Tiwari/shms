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


    @staticmethod
    @transaction.atomic
    def update_patient(
        *,
        user,
        patient,
        user_data,
        patient_data,
    ):
        """
        Update existing User and Patient records.
        """

        user.first_name = user_data["first_name"]
        user.last_name = user_data["last_name"]
        user.email = user_data["email"]
        user.phone_number = user_data["phone_number"]

        if user_data.get("password"):
            user.set_password(user_data["password"])

        user.save()

        for field, value in patient_data.items():
            setattr(patient, field, value)

        patient.save()

        return patient

    @staticmethod
    @transaction.atomic
    def delete_patient(*, patient):
        """
        Delete Patient and associated User.
        """

        user = patient.user

        user.delete()