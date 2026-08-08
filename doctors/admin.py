from django.contrib import admin

from .models import Doctor


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