from django.contrib import admin

from .models import Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = (
        "patient_id",
        "user",
        "gender",
        "blood_group",
        "city",
        "created_at",
    )

    list_filter = (
        "gender",
        "blood_group",
        "city",
        "state",
    )

    search_fields = (
        "patient_id",
        "user__email",
        "user__first_name",
        "user__last_name",
        "city",
    )

    ordering = ("-created_at",)

    readonly_fields = (
        "patient_id",
        "created_at",
        "updated_at",
    )

    fieldsets = (
        (
            "Basic Information",
            {
                "fields": (
                    "user",
                    "patient_id",
                    "date_of_birth",
                    "gender",
                    "blood_group",
                )
            },
        ),
        (
            "Contact Information",
            {
                "fields": (
                    "emergency_contact",
                    "address",
                    "city",
                    "state",
                    "pincode",
                )
            },
        ),
        (
            "Medical Information",
            {
                "fields": (
                    "allergies",
                    "medical_history",
                )
            },
        ),
        (
            "Audit Information",
            {
                "fields": (
                    "created_at",
                    "updated_at",
                )
            },
        ),
    )