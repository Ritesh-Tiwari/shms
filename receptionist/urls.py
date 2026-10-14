from django.urls import path

from . import views


app_name = "receptionist"


urlpatterns = [

    path(
        "",
        views.dashboard,
        name="dashboard",
    ),
    path(
        "list/",
        views.receptionist_list,
        name="list",
    ),

    path(
        "create/",
        views.create_receptionist,
        name="create",
    ),

    path(
        "<int:pk>/",
        views.receptionist_detail,
        name="detail",
    ),

    path(
        "<int:pk>/update/",
        views.update_receptionist,
        name="update",
    ),

    path(
        "<int:pk>/delete/",
        views.delete_receptionist,
        name="delete",
    ),

    path(
        "appointments/",
        views.appointment_list,
        name="appointments",
    ),

    path(
        "appointments/<int:pk>/check-in/",
        views.check_in,
        name="check-in",
    ),

]