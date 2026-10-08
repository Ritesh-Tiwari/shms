from django.db import models
from appointments.models import Appointment

class PrescriptionStatus(models.TextChoices):
    ACTIVE = "ACTIVE", "Active"
    COMPLETED = "COMPLETED", "Completed"

class Prescription(models.Model):

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="prescription",
    )

    prescription_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )
    

    diagnosis = models.TextField()

    remarks = models.TextField(
        blank=True,
    )

    status = models.CharField(
        max_length=20,
        choices=PrescriptionStatus.choices,
        default=PrescriptionStatus.ACTIVE,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        db_table = "prescriptions"

        ordering = [
            "-created_at",
        ]

        verbose_name = "Prescription"

        verbose_name_plural = "Prescriptions"

    def __str__(self):

        return self.prescription_id
    
    @property
    def is_active(self):
        return self.status == PrescriptionStatus.ACTIVE

    @property
    def status_label(self): 
        return self.get_status_display()
    

    def save(self, *args, **kwargs):

        if not self.prescription_id:

            last_prescription = (
                Prescription.objects.order_by("-id").first()
            )

            if last_prescription:

                last_id = int(
                    last_prescription.prescription_id.replace(
                        "PRE",
                        ""
                    )
                )

                self.prescription_id = (
                    f"PRE{last_id + 1:06d}"
                )

            else:

                self.prescription_id = "PRE000001"

        super().save(*args, **kwargs)


class PrescriptionMedicine(models.Model):

    prescription = models.ForeignKey(
        Prescription,
        on_delete=models.CASCADE,
        related_name="medicines",
    )

    medicine_name = models.CharField(
        max_length=200,
    )

    dosage = models.CharField(
        max_length=100,
    )

    frequency = models.CharField(
        max_length=100,
    )

    duration = models.CharField(
        max_length=100,
    )

    instructions = models.TextField(
        blank=True,
    )

    class Meta:

        db_table = "prescription_medicines"

        ordering = [
            "id",
        ]

        verbose_name = "Prescription Medicine"

        verbose_name_plural = "Prescription Medicines"

    def __str__(self):

        return self.medicine_name 