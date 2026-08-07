from django.urls import path

from . import views

app_name = "doctors"

urlpatterns = [

    path(
        "register/",
        views.register_doctor,
        name="register",
    ),

    path(
        "list/",
        views.doctor_list,
        name="list",
    ),

    path(
        "<int:pk>/",
        views.doctor_detail,
        name="detail",
    ),

    path(
        "<int:pk>/update/",
        views.update_doctor,
        name="update",
    ),
    
    path(
        "<int:pk>/delete/",
        views.delete_doctor,
        name="delete",
    ),
]