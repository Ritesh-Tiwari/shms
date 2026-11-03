from django.urls import path

from security_audit.views import audit_log_list

from . import reports, views

app_name = "dashboard"

urlpatterns = [
    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "accounts/",
        views.account_list,
        name="accounts",
    ),
    path(
        "accounts/<int:pk>/toggle-status/",
        views.toggle_account_status,
        name="toggle-status",
    ),
    path(
        "security-audit/",
        audit_log_list,
        name="security-audit",
    ),
    path(
        "reports/",
        reports.report_list,
        name="reports",
    ),
    path(
        "reports/download/",
        reports.report_download,
        name="report-download",
    ),
]