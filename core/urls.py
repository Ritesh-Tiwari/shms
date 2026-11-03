from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("search/", views.global_search, name="search"),
    path(
        "notifications/read/",
        views.mark_notifications_read,
        name="notifications-mark-read",
    ),
    path(
        "notifications/<int:pk>/open/",
        views.open_notification,
        name="notification-open",
    ),
]
