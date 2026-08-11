from django.urls import path

from . import views


app_name = "prescriptions"


urlpatterns = [

    path(
        "create/<int:appointment_id>/",
        views.create_prescription,
        name="create",
    ),
    path(
        "<int:pk>/",
        views.prescription_detail,
        name="detail",
    ),

    path(
        "<int:pk>/update/",
        views.update_prescription,
        name="update",
    ),
]