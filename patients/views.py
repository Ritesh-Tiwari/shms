from django.contrib import messages
from django.shortcuts import redirect, render
from django.http import HttpResponse

from .models import Patient
from accounts.forms import UserRegistrationForm
from .forms import PatientForm
from .services import PatientService


def home(request):
    return render(request, "patients/home.html")


def register_patient(request):

    if request.method == "POST":

        user_form = UserRegistrationForm(request.POST)

        patient_form = PatientForm(request.POST)

        if user_form.is_valid() and patient_form.is_valid():

            PatientService.create_patient(

                user_data=user_form.cleaned_data,

                patient_data=patient_form.cleaned_data,

            )

            messages.success(
                request,
                "Patient registered successfully.",
            )

            return redirect("patients:list")

    else:

        user_form = UserRegistrationForm()

        patient_form = PatientForm()

    context = {

        "user_form": user_form,

        "patient_form": patient_form,

    }

    return render(
        request,
        "patients/register.html",
        context,
    )

def patient_list(request):

    patients = Patient.objects.select_related("user")

    return render(
        request,
        "patients/list.html",
        {
            "patients": patients,
        },
    )

