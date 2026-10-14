from django.contrib import admin

from .models import Receptionist


@admin.register(Receptionist)
class ReceptionistAdmin(admin.ModelAdmin):

    list_display = (
        "receptionist_id",
        "get_full_name",
        "get_email",
        "joining_date",
        "created_at",
    )

    search_fields = (
        "receptionist_id",
        "user__username",
        "user__first_name",
        "user__last_name",
        "user__email",
        "user__phone_number",
    )

    list_filter = (
        "joining_date",
        "created_at",
    )

    readonly_fields = (
        "receptionist_id",
        "created_at",
        "updated_at",
    )

    def get_full_name(self, obj):

        return obj.user.get_full_name()

    get_full_name.short_description = "Full Name"

    def get_email(self, obj):

        return obj.user.email

    get_email.short_description = "Email"