from django.conf import settings
from django.db import models

from .choices import AvailabilityChoices, SpecializationChoices


class Doctor(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="doctor_profile",
    )

    doctor_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    specialization = models.CharField(
        max_length=50,
        choices=SpecializationChoices.choices,
    )

    qualification = models.CharField(
        max_length=200,
    )

    experience = models.PositiveIntegerField()

    consultation_fee = models.DecimalField(
        max_digits=8,
        decimal_places=2,
    )

    availability = models.CharField(
        max_length=20,
        choices=AvailabilityChoices.choices,
        default=AvailabilityChoices.AVAILABLE,
    )

    address = models.TextField()

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        db_table = "doctors"

        ordering = [
            "doctor_id",
        ]

        verbose_name = "Doctor"

        verbose_name_plural = "Doctors"

    def __str__(self):

        return f"{self.doctor_id} - {self.user.get_full_name()}"

    def save(self, *args, **kwargs):

        if not self.doctor_id:

            last_doctor = Doctor.objects.order_by("-id").first()

            if last_doctor:

                last_id = int(
                    last_doctor.doctor_id.replace("DOC", "")
                )

                self.doctor_id = f"DOC{last_id + 1:06d}"

            else:

                self.doctor_id = "DOC000001"

        super().save(*args, **kwargs)