from django.urls import path

from . import views


app_name = "prescriptions"


urlpatterns = [

    # Patient read-only access

    path(
        "my/",
        views.my_prescriptions,
        name="my-prescriptions",
    ),

    path(
        "my/<int:pk>/",
        views.my_prescription_detail,
        name="my-prescription-detail",
    ),


    # Staff

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