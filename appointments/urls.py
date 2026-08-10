from django.urls import path

from . import views


app_name = "appointments"

urlpatterns = [

    path(
        "",
        views.appointment_list,
        name="list",
    ),

    path(
        "create/",
        views.create_appointment,
        name="create",
    ),

    path(
        "<int:pk>/",
        views.appointment_detail,
        name="detail",
    ),

    path(
        "<int:pk>/update/",
        views.update_appointment,
        name="update",
    ),

    path(
        "<int:pk>/cancel/",
        views.cancel_appointment,
        name="cancel",
    ),

    path(
    "<int:pk>/status/",
    views.update_appointment_status,
    name="update_status",
),
]