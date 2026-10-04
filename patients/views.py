import logging

from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.http import HttpResponse
from django.db import transaction
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator

from appointments.models import Appointment
from .models import Patient
from accounts.forms import UserRegistrationForm, PatientOwnAccountForm
from .forms import PatientForm, PatientOwnProfileForm
from .services import PatientService
from core.decorators import role_required
from accounts.choices import UserRole


logger = logging.getLogger(__name__)


def home(request):
    return render(request, "patients/home.html")


@role_required(
    UserRole.ADMIN,
)
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


@role_required(UserRole.ADMIN)
def patient_list(request):

    query = request.GET.get("q", "").strip()

    last_appointments = (
        Appointment.objects
        .select_related("doctor__user")
        .order_by("-appointment_date", "-id")
    )

    patients = (
        Patient.objects
        .select_related("user")
        .prefetch_related(
            Prefetch(
                "appointments",
                queryset=last_appointments,
                to_attr="patient_appointments",
            )
        )
    )

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


@role_required(
    UserRole.ADMIN,
)
def patient_detail(request, pk):

    patient = get_object_or_404(
        Patient.objects.select_related("user"),
        pk=pk,
    )

    appointments = (
        patient.appointments
        .select_related("doctor__user")
        .order_by(
            "-appointment_date",
            "-appointment_time",
        )
    )

    return render(
        request,
        "patients/detail.html",
        {
            "patient": patient,
            "appointments": appointments,
        },
    )


@role_required(
    UserRole.ADMIN,
)
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


@role_required(
    UserRole.ADMIN,
)
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


@role_required(UserRole.PATIENT)
def my_profile(request):
    """
    Show the currently authenticated patient's own profile.

    The patient is resolved from request.user rather than a URL id,
    preventing one patient from requesting another patient's profile.
    """
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(
            request,
            "Your patient profile could not be found. Please contact an administrator.",
        )
        return redirect("dashboard:dashboard")

    return render(
        request,
        "patients/my_profile.html",
        {"patient": patient},
    )


@role_required(UserRole.PATIENT)
def edit_my_profile(request):
    """
    Allow a patient to edit only their own contact/address fields.

    Clinical information is deliberately excluded from the forms.
    Both model saves happen inside one transaction so a partial update
    cannot leave the profile in an inconsistent state.
    """
    try:
        patient = request.user.patient_profile
    except Patient.DoesNotExist:
        messages.error(
            request,
            "Your patient profile could not be found. Please contact an administrator.",
        )
        return redirect("dashboard:dashboard")

    if request.method == "POST":
        user_form = PatientOwnAccountForm(
            request.POST,
            instance=request.user,
        )
        patient_form = PatientOwnProfileForm(
            request.POST,
            instance=patient,
        )

        user_valid = user_form.is_valid()
        patient_valid = patient_form.is_valid()

        if user_valid and patient_valid:
            try:
                with transaction.atomic():
                    user_form.save()
                    patient_form.save()

                messages.success(
                    request,
                    "Your profile has been updated successfully.",
                )
                return redirect("patients:my-profile")

            except Exception:
                logger.exception(
                    "Patient self-profile update failed for user_id=%s",
                    request.user.pk,
                )
                messages.error(
                    request,
                    "Profile update failed due to a server error. Please try again. If the problem continues, contact an administrator.",
                )
        else:
            messages.error(
                request,
                "Profile was not saved. Please correct the highlighted errors below.",
            )

    else:
        user_form = PatientOwnAccountForm(
            instance=request.user,
        )
        patient_form = PatientOwnProfileForm(
            instance=patient,
        )

    return render(
        request,
        "patients/edit_my_profile.html",
        {
            "patient": patient,
            "user_form": user_form,
            "patient_form": patient_form,
        },
    )
