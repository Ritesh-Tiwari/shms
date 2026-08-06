from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_patient, name="register"),
    path("list/", views.patient_list, name="list"),
    path("<int:pk>/", views.patient_detail, name="detail"),

    path(
    "<int:pk>/edit/",
    views.update_patient,
    name="update",
),
]