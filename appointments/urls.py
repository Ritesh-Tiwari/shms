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

]