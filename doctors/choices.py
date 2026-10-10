from django.db import models


class SpecializationChoices(models.TextChoices):

    GENERAL_PHYSICIAN = "GENERAL_PHYSICIAN", "General Physician"
    CARDIOLOGIST = "CARDIOLOGIST", "Cardiologist"
    DERMATOLOGIST = "DERMATOLOGIST", "Dermatologist"
    ENT = "ENT", "ENT Specialist"
    GYNECOLOGIST = "GYNECOLOGIST", "Gynecologist"
    NEUROLOGIST = "NEUROLOGIST", "Neurologist"
    OPHTHALMOLOGIST = "OPHTHALMOLOGIST", "Ophthalmologist"
    ORTHOPEDIC = "ORTHOPEDIC", "Orthopedic"
    PEDIATRICIAN = "PEDIATRICIAN", "Pediatrician"
    PSYCHIATRIST = "PSYCHIATRIST", "Psychiatrist"
    RADIOLOGIST = "RADIOLOGIST", "Radiologist"
    SURGEON = "SURGEON", "Surgeon"


class AvailabilityChoices(models.TextChoices):

    AVAILABLE = "AVAILABLE", "Available"
    ON_LEAVE = "ON_LEAVE", "On Leave"
    NOT_AVAILABLE = "NOT_AVAILABLE", "Not Available"

class Weekday(models.IntegerChoices):
    MONDAY = 0, "Monday"
    TUESDAY = 1, "Tuesday"
    WEDNESDAY = 2, "Wednesday"
    THURSDAY = 3, "Thursday"
    FRIDAY = 4, "Friday"
    SATURDAY = 5, "Saturday"
    SUNDAY = 6, "Sunday"