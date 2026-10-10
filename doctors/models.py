from django.conf import settings
from django.db import models

from .choices import AvailabilityChoices, SpecializationChoices, Weekday


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

    @property
    def badge_bg_class(self):
        spec = str(self.specialization).upper().strip()
        colors = {
            'GENERAL_PHYSICIAN': 'bg-slate-100 text-slate-800',
            'CARDIOLOGIST': 'bg-rose-100 text-rose-800',
            'DERMATOLOGIST': 'bg-purple-100 text-purple-800',
            'ENT': 'bg-teal-100 text-teal-800',
            'GYNECOLOGIST': 'bg-pink-100 text-pink-800',
            'NEUROLOGIST': 'bg-cyan-100 text-cyan-800',
            'OPHTHALMOLOGIST': 'bg-emerald-100 text-emerald-800',
            'ORTHOPEDIC': 'bg-blue-100 text-blue-800',
            'PEDIATRICIAN': 'bg-amber-100 text-amber-800',
            'PSYCHIATRIST': 'bg-violet-100 text-violet-800',
            'RADIOLOGIST': 'bg-indigo-100 text-indigo-800',
            'SURGEON': 'bg-orange-100 text-orange-800',
        }
        return colors.get(self.specialization, 'bg-gray-100 text-gray-800')

    @property
    def badge_dot_class(self):
        spec = str(self.specialization).upper().strip()
        dots = {
            'GENERAL_PHYSICIAN': 'bg-slate-500',
            'CARDIOLOGIST': 'bg-rose-500',
            'DERMATOLOGIST': 'bg-purple-500',
            'ENT': 'bg-teal-500',
            'GYNECOLOGIST': 'bg-pink-500',
            'NEUROLOGIST': 'bg-cyan-500',
            'OPHTHALMOLOGIST': 'bg-emerald-500',
            'ORTHOPEDIC': 'bg-blue-500',
            'PEDIATRICIAN': 'bg-amber-500',
            'PSYCHIATRIST': 'bg-violet-500',
            'RADIOLOGIST': 'bg-indigo-500',
            'SURGEON': 'bg-orange-500',
        }
        return dots.get(self.specialization, 'bg-gray-500')
    
    
    @property
    def status_badge_class(self):
        # Availability choices matching
        status = str(self.availability).upper().strip()
        
        styles = {
            'AVAILABLE': 'bg-emerald-100 text-emerald-800 border-emerald-200',
            'ON_LEAVE': 'bg-amber-100 text-amber-800 border-amber-200',
            'NOT_AVAILABLE': 'bg-rose-100 text-rose-800 border-rose-200',
        }
        return styles.get(status, 'bg-gray-100 text-gray-800 border-gray-200')

    @property
    def status_icon(self):
        status = str(self.availability).upper().strip()
        
        icons = {
            'AVAILABLE': 'check_circle',
            'ON_LEAVE': 'flight_takeoff',
            'NOT_AVAILABLE': 'cancel',
        }
        return icons.get(status, 'help')
    
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

class DoctorSchedule(models.Model):   

    doctor = models.ForeignKey(
        Doctor,
        on_delete=models.CASCADE,
        related_name="schedules",
    )

    weekday = models.PositiveSmallIntegerField(
        choices=Weekday.choices,
    )

    start_time = models.TimeField()
    end_time = models.TimeField()

    is_active = models.BooleanField(default=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "doctor_schedules"
        ordering = ["weekday", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "weekday", "start_time"],
                name="unique_doctor_weekday_start",
            ),
        ]

    def clean(self):
        from django.core.exceptions import ValidationError

        if self.start_time and self.end_time:
            if self.start_time >= self.end_time:
                raise ValidationError({
                    "end_time": "End time must be later than start time."
                })

    def __str__(self):
        return (
            f"{self.doctor.doctor_id} - "
            f"{self.get_weekday_display()} "
            f"{self.start_time}-{self.end_time}"
        )