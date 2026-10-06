from datetime import date
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
                condition=models.Q(
                    status__in=[
                        AppointmentStatus.SCHEDULED,
                        AppointmentStatus.CONFIRMED,
                    ]
                ),
                name="unique_active_doctor_appointment_slot",
            ),

        ]

    def __str__(self):
        return (
            f"{self.appointment_id} - "
            f"{self.patient.patient_id} - "
            f"{self.doctor.doctor_id}"
        )
    
    @property
    def status_color_classes(self):
        color_map = {
            'SCHEDULED': {'bg': 'bg-emerald-50', 'text': 'text-emerald-700', 'dot': 'bg-emerald-500'},
            'CONFIRMED': {'bg': 'bg-emerald-50', 'text': 'text-emerald-700', 'dot': 'bg-emerald-500'},
            'PENDING':   {'bg': 'bg-amber-50',   'text': 'text-amber-700',   'dot': 'bg-amber-500'},
            'CANCELLED': {'bg': 'bg-rose-50',    'text': 'text-rose-700',    'dot': 'bg-rose-500'},
            'COMPLETED': {'bg': 'bg-blue-50',    'text': 'text-blue-700',    'dot': 'bg-blue-500'},
        }
        return color_map.get(
            self.status, 
            {'bg': 'bg-slate-100', 'text': 'text-slate-700', 'dot': 'bg-slate-500'}
        )

    @property
    def is_upcoming(self):
        # Current date ya status ke basis par logic
        return self.status in ['SCHEDULED', 'CONFIRMED', 'PENDING'] and self.appointment_date >= date.today()

    @property
    def appointment_type(self):
        return "upcoming" if self.is_upcoming else "past"

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