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
        "dashboard/",
        views.doctor_dashboard,
        name="dashboard",
    ),
    path(
        "<int:pk>/toggle-active/",
        views.toggle_doctor_active,
        name="toggle-active",
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

    path(
        "my-schedule/",
        views.my_schedule,
        name="schedule",
    ), 
    path(
        "my-schedule/add/",
        views.add_schedule,
        name="schedule-add",
    ),
    path(
        "my-schedule/<int:pk>/delete/",
        views.delete_schedule,
        name="schedule-delete",
    ),
    path(
        "my-patients/",
        views.my_patients,
        name="my-patients",
    ),
    path(
        "my-patients/<int:pk>/",
        views.patient_clinical_summary,
        name="patient-summary",
    ),
]