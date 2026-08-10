from django.db import IntegrityError, transaction

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