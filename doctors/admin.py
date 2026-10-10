from django.contrib import admin

from .models import Doctor, DoctorSchedule


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):

    list_display = (
        "doctor_id",
        "user",
        "specialization",
        "experience",
        "consultation_fee",
        "availability",
    )

    search_fields = (
        "doctor_id",
        "user__first_name",
        "user__last_name",
        "user__email",
    )

    list_filter = (
        "specialization",
        "availability",
    )

    ordering = (
        "doctor_id",
    )

@admin.register(DoctorSchedule)
class DoctorScheduleAdmin(admin.ModelAdmin):
    list_display = (
        "doctor",
        "weekday",
        "start_time",
        "end_time",
        "is_active",
    )

    list_filter = (
        "weekday",
        "is_active",
    )

    search_fields = (
        "doctor__doctor_id",
        "doctor__user__first_name",
        "doctor__user__last_name",
    )