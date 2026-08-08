from django.db import models

from doctors.models import Doctor
from patients.models import Patient


class AppointmentStatus(models.TextChoices):
    SCHEDULED = "SCHEDULED", "Scheduled"
    CONFIRMED = "CONFIRMED", "Confirmed"
    COMPLETED = "COMPLETED", "Completed"
    CANCELLED = "CANCELLED", "Cancelled"


class Appointment(models.Model):

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="appointments",
    )

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="appointments",
    )

    appointment_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    appointment_date = models.DateField()

    appointment_time = models.TimeField()

    reason_for_visit = models.CharField(
        max_length=255,
    )

    status = models.CharField(
        max_length=20,
        choices=AppointmentStatus.choices,
        default=AppointmentStatus.SCHEDULED,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "appointments"

        ordering = [
            "appointment_date",
            "appointment_time",
        ]

        constraints = [
            models.UniqueConstraint(
                fields=[
                    "doctor",
                    "appointment_date",
                    "appointment_time",
                ],
                name="unique_doctor_appointment_slot",
            ),
        ]

    def __str__(self):
        return (
            f"{self.appointment_id} - "
            f"{self.patient.patient_id} - "
            f"{self.doctor.doctor_id}"
        )

    def save(self, *args, **kwargs):

        if not self.appointment_id:

            last_appointment = (
                Appointment.objects.order_by("-id").first()
            )

            if last_appointment:

                last_id = int(
                    last_appointment.appointment_id.replace(
                        "APT",
                        ""
                    )
                )

                self.appointment_id = (
                    f"APT{last_id + 1:06d}"
                )

            else:

                self.appointment_id = "APT000001"

        super().save(*args, **kwargs)