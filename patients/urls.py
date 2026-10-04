from django.urls import path

from . import views

app_name = "patients"

urlpatterns = [
    path("", views.home, name="home"),
    path("register/", views.register_patient, name="register"),
    path("list/", views.patient_list, name="list"),

    # Patient self-service routes must come before <int:pk>/.
    path("profile/", views.my_profile, name="my-profile"),
    path("profile/edit/", views.edit_my_profile, name="edit-my-profile"),

    path("<int:pk>/", views.patient_detail, name="detail"),

    path(
        "<int:pk>/edit/",
        views.update_patient,
        name="update",
    ),

    path(
        "<int:pk>/delete/",
        views.delete_patient,
        name="delete",
    ),
]
