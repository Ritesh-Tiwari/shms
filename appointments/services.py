from datetime import datetime

from django.db import IntegrityError, transaction
from django.utils import timezone

from .models import Appointment, AppointmentStatus
class AppointmentService:

    @staticmethod
    def create_appointment(
        appointment_data,
    ):

        try:

            with transaction.atomic():

                appointment = Appointment.objects.create(
                    **appointment_data,
                )

                return appointment

        except IntegrityError:

            raise ValueError(
                "This doctor already has an appointment "
                "at the selected date and time."
            )

    @staticmethod
    def update_appointment(
        appointment,
        appointment_data,
    ):

        try:

            with transaction.atomic():

                appointment.appointment_date = (
                    appointment_data["appointment_date"]
                )

                appointment.appointment_time = (
                    appointment_data["appointment_time"]
                )

                appointment.reason_for_visit = (
                    appointment_data["reason_for_visit"]
                )

                appointment.save()

                return appointment

        except IntegrityError:

            raise ValueError(
                "This doctor already has an appointment "
                "at the selected date and time."
            )

    @staticmethod
    def cancel_appointment(
        appointment,
    ):

        if appointment.status == AppointmentStatus.COMPLETED:

            raise ValueError(
                "Completed appointments cannot be cancelled."
            )

        if appointment.status == AppointmentStatus.CANCELLED:

            raise ValueError(
                "Appointment is already cancelled."
            )

        appointment.status = AppointmentStatus.CANCELLED

        appointment.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

        return appointment

    @staticmethod
    def update_status(
        appointment,
        new_status,
    ):

        allowed_transitions = {

            AppointmentStatus.SCHEDULED: [
                AppointmentStatus.CONFIRMED,
                AppointmentStatus.CANCELLED,
            ],

            AppointmentStatus.CONFIRMED: [
                AppointmentStatus.COMPLETED,
                AppointmentStatus.CANCELLED,
            ],

            AppointmentStatus.COMPLETED: [],

            AppointmentStatus.CANCELLED: [],
        }

        if new_status not in allowed_transitions.get(
            appointment.status,
            [],
        ):

            raise ValueError(
                f"Cannot change appointment status "
                f"from {appointment.get_status_display()} "
                f"to {new_status}."
            )

        if new_status == AppointmentStatus.COMPLETED:

            now = timezone.localtime()

            appointment_datetime = timezone.make_aware(
                datetime.combine(
                    appointment.appointment_date,
                    appointment.appointment_time,
                )
            )

            if appointment_datetime > now:

                raise ValueError(
                    "Appointment cannot be marked as "
                    "completed before its scheduled date and time."
                )

        appointment.status = new_status

        appointment.save(
            update_fields=[
                "status",
                "updated_at",
            ],
        )

        return appointment