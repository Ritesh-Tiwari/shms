from django.urls import path

from . import views

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
]