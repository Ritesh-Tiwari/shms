from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from appointments.models import (
    Appointment,
    AppointmentStatus,
)
from accounts.models import User
from accounts.choices import UserRole
from .models import Receptionist


class ReceptionistService:

    @staticmethod
    @transaction.atomic
    def create_receptionist(
        *,
        user_data,
        profile_data,
    ):

        user = User.objects.create_user(

            username=user_data["username"],

            email=user_data["email"],

            password=user_data["password"],

            first_name=user_data["first_name"],

            last_name=user_data["last_name"],

            phone_number=user_data["phone_number"],

            role=UserRole.RECEPTIONIST,
        )

        receptionist = Receptionist.objects.create(

            user=user,

            **profile_data,
        )

        return receptionist

    @staticmethod
    @transaction.atomic
    def update_receptionist(
        *,
        receptionist,
        user_data,
        profile_data,
    ):

        user = receptionist.user

        user.username = user_data["username"]

        user.first_name = user_data["first_name"]

        user.last_name = user_data["last_name"]

        user.email = user_data["email"]

        user.phone_number = user_data["phone_number"]

        password = user_data.get("password")

        if password:

            user.set_password(password)

        # Preserve the correct account role.
        user.role = UserRole.RECEPTIONIST

        user.save()

        for field, value in profile_data.items():

            setattr(
                receptionist,
                field,
                value,
            )

        receptionist.save()

        return receptionist

    @staticmethod
    @transaction.atomic
    def delete_receptionist(
        *,
        receptionist,
    ):

        user = receptionist.user

        # The Receptionist profile will be deleted
        # automatically through CASCADE.
        user.delete()


class ReceptionistService:

    @staticmethod
    @transaction.atomic
    def check_in_appointment(*, appointment_id):

        try:
            appointment = (
                Appointment.objects
                .select_for_update()
                .get(pk=appointment_id)
            )

        except Appointment.DoesNotExist:
            raise ValidationError(
                "Appointment not found."
            )

        if appointment.status == AppointmentStatus.CANCELLED:
            raise ValidationError(
                "Cancelled appointments cannot be checked in."
            )

        if appointment.status == AppointmentStatus.COMPLETED:
            raise ValidationError(
                "Completed appointments cannot be checked in."
            )

        if appointment.checked_in_at is not None:
            raise ValidationError(
                "This appointment has already been checked in."
            )

        appointment.checked_in_at = timezone.now()

        appointment.save(
            update_fields=[
                "checked_in_at",
                "updated_at",
            ]
        )

        return appointment