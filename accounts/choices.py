# custom file
# enum for user roles

from django.db import models


class UserRole(models.TextChoices):
    ADMIN = "ADMIN", "Admin"
    DOCTOR = "DOCTOR", "Doctor"
    PATIENT = "PATIENT", "Patient"
    RECEPTIONIST = "RECEPTIONIST", "Receptionist"