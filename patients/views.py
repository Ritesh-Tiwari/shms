from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from django.db.models import Q
from django.core.paginator import Paginator
from django.contrib.auth.decorators import login_required


from .models import Patient
from accounts.forms import UserRegistrationForm
from .forms import PatientForm
from .services import PatientService
from core.decorators import role_required
from accounts.choices import UserRole


def home(request):
    return render(request, "patients/home.html")

@login_required
# @role_required(
#     UserRole.ADMIN,
#     UserRole.RECEPTIONIST,
# )
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

@login_required
# @role_required(
#     UserRole.ADMIN,
#     UserRole.RECEPTIONIST,
#     UserRole.DOCTOR,
# )
def patient_list(request):

    query = request.GET.get("q", "").strip()

    patients = Patient.objects.select_related("user")

    if query:

        patients = patients.filter(

            Q(patient_id__icontains=query)

            | Q(user__first_name__icontains=query)

            | Q(user__last_name__icontains=query)

            | Q(user__email__icontains=query)

            | Q(user__phone_number__icontains=query)

        )

    paginator = Paginator(
        patients,
        10,
    )

    page_number = request.GET.get("page")

    page_obj = paginator.get_page(
        page_number,
    )


    return render(
        request,
        "patients/list.html",
        {
            "patients": page_obj,
            "page_obj": page_obj,
            "query": query,
        },
    )


# @role_required(
#     UserRole.ADMIN,
#     UserRole.RECEPTIONIST,
#     UserRole.DOCTOR,
# )
@login_required
def patient_detail(request, pk):

    patient = get_object_or_404(
        Patient.objects.select_related("user"),
        pk=pk,
    )

    return render(
        request,
        "patients/detail.html",
        {
            "patient": patient,
        },
    )



# @role_required(
#     UserRole.ADMIN,
#     UserRole.RECEPTIONIST,
# )
@login_required
def update_patient(request, pk):

    patient = get_object_or_404(
        Patient.objects.select_related("user"),
        pk=pk,
    )

    if request.method == "POST":

        user_form = UserRegistrationForm(
            request.POST,
            instance=patient.user,
        )

        patient_form = PatientForm(
            request.POST,
            instance=patient,
        )

        if user_form.is_valid() and patient_form.is_valid():

            PatientService.update_patient(

                user=patient.user,

                patient=patient,

                user_data=user_form.cleaned_data,

                patient_data=patient_form.cleaned_data,

            )

            messages.success(
                request,
                "Patient updated successfully.",
            )

            return redirect(
                "patients:detail",
                pk=patient.pk,
            )

    else:

        user_form = UserRegistrationForm(
            instance=patient.user,
        )

        patient_form = PatientForm(
            instance=patient,
        )

    return render(
        request,
        "patients/update.html",
        {
            "user_form": user_form,
            "patient_form": patient_form,
            "patient": patient,
        },
    )

# @role_required(
#     UserRole.ADMIN,
#     UserRole.RECEPTIONIST,
# )
@login_required
def delete_patient(request, pk):

    patient = get_object_or_404(
        Patient.objects.select_related("user"),
        pk=pk,
    )

    if request.method == "POST":

        PatientService.delete_patient(
            patient=patient,
        )

        messages.success(
            request,
            "Patient deleted successfully.",
        )

        return redirect("patients:list")

    return render(
        request,
        "patients/delete.html",
        {
            "patient": patient,
        },
    )