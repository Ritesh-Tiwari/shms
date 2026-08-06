from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [

    path(
        "",
        views.home,
        name="home",
    ),

    path(
        "register/",
        views.register_patient,
        name="register",
    ),

    path(
        "list/",
        views.patient_list,
        name="list",
    ),

]