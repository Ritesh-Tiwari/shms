from django.contrib import admin

from accounts.choices import UserRole

from .models import AuditLog


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = (
        "timestamp",
        "actor",
        "action",
        "outcome",
        "target_identifier",
        "ip_address",
    )
    list_filter = ("action", "outcome", "timestamp")
    search_fields = ("actor__email", "target_identifier", "action")
    readonly_fields = (
        "actor",
        "action",
        "target_user",
        "target_identifier",
        "outcome",
        "timestamp",
        "ip_address",
        "user_agent",
        "details",
    )

    def has_add_permission(self, request):
        return False

    def has_module_permission(self, request):
        return self.has_view_permission(request)

    def has_view_permission(self, request, obj=None):
        return request.user.is_superuser or (
            request.user.is_authenticated
            and request.user.role == UserRole.ADMIN
        )

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
