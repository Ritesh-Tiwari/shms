from django.db import models
from django.conf import settings

from .choices import GenderChoices, BloodGroupChoices

class Patient(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="patient_profile",
    )
    patient_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    date_of_birth = models.DateField()

    gender = models.CharField(
        max_length=10,
        choices=GenderChoices.choices,
    )

    blood_group = models.CharField(
        max_length=5,
        choices=BloodGroupChoices.choices,
    )

    emergency_contact = models.CharField(
        max_length=15,
    )

    address = models.TextField()

    city = models.CharField(
        max_length=100,
    )

    state = models.CharField(
        max_length=100,
    )

    pincode = models.CharField(
        max_length=10,
    )

    allergies = models.TextField(
        blank=True,
    )

    medical_history = models.TextField(
        blank=True,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:
        db_table = "patients"
        verbose_name = "Patient"
        verbose_name_plural = "Patients"

    def __str__(self):
        return self.patient_id

    def save(self, *args, **kwargs):
        if not self.patient_id:
            last_patient = (
                Patient.objects.order_by("-id").first()
            )

            if last_patient:
                last_id = int(last_patient.patient_id.replace("PAT", ""))
                self.patient_id = f"PAT{last_id + 1:06d}"
            else:
                self.patient_id = "PAT000001"

        super().save(*args, **kwargs)