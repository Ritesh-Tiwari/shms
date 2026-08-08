from django.db import IntegrityError, transaction

from .models import Appointment


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