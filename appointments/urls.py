from django.urls import path

from . import views


app_name = "appointments"


urlpatterns = [

    # -------------------------
    # Patient
    # -------------------------

    path(
        "my/",
        views.my_appointments,
        name="my-appointments",
    ),

    path(
        "my/book/",
        views.book_appointment,
        name="book",
    ),

    path(
        "my/<int:pk>/",
        views.my_appointment_detail,
        name="my-appointment-detail",
    ),
    path(
        "my/<int:pk>/reschedule/",
        views.my_reschedule_appointment,
        name="my-reschedule",
    ),

    path(
        "my/<int:pk>/cancel/",
        views.my_cancel_appointment,
        name="my-cancel",
    ),


    # -------------------------
    # Staff
    # -------------------------

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