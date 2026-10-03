from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.db.models import Q, Prefetch, Sum
from django.core.paginator import Paginator
from django.utils import timezone

from decimal import Decimal

from appointments.models import Appointment
from .models import Patient
from accounts.forms import UserRegistrationForm
from .forms import PatientForm
from .services import PatientService
from core.decorators import role_required
from accounts.choices import UserRole
from prescriptions.models import Prescription


@role_required(UserRole.PATIENT)
def home(request):
    patient = get_object_or_404(Patient.objects.select_related("user"), user=request.user)

    upcoming_appointments = (
        patient.appointments
        .filter(appointment_date__gte=timezone.localdate())
        .exclude(status="CANCELLED")
        .select_related("doctor__user")
        .order_by("appointment_date", "appointment_time")[:5]
    )
    recent_appointments = (
        patient.appointments
        .exclude(status="CANCELLED")
        .filter(appointment_date__lt=timezone.localdate())
        .select_related("doctor__user")
        .order_by("-appointment_date", "-appointment_time")[:5]
    )
    

    next_appointment = upcoming_appointments.first()
    last_visit_date = recent_appointments.first().appointment_date if recent_appointments.exists() else None
    total_visits = patient.appointments.exclude(status="CANCELLED").filter(appointment_date__lt=timezone.localdate()).count()

    current_prescription = (
        Prescription.objects
        .filter(appointment__patient=patient)
        .select_related("appointment__doctor__user")
        .prefetch_related("medicines")
        .order_by("-created_at")
        .first()
    )

    total_active_medicines = sum(
            prescription.medicines.count()
            for prescription in (
                Prescription.objects
                .filter(appointment__patient=patient)
                .prefetch_related("medicines")
            )
        )

    latest_bill = (
        patient.bills
        .select_related("appointment")
        .prefetch_related("payments")
        .order_by("-bill_date")
        .first()
    )

    if latest_bill:
        total_paid = latest_bill.payments.aggregate(total=Sum("amount"))["total"] or Decimal("0.00")
        balance_due = max(latest_bill.total_amount - total_paid, Decimal("0.00"))
        latest_payment = latest_bill.payments.order_by("-payment_date").first()
    else:
        total_paid = Decimal("0.00")
        balance_due = Decimal("0.00")
        latest_payment = None

    return render(
        request,
        "patients/home.html",
        {
            "patient": patient,
            "upcoming_appointments": upcoming_appointments,
            "recent_appointments": recent_appointments,
            "next_appointment": next_appointment,
            "current_prescription": current_prescription,
            "total_active_medicines": total_active_medicines,
            "total_visits": total_visits,
            "balance_due": balance_due,
            "latest_bill": latest_bill,
            "latest_payment": latest_payment,
            "last_visit_date": last_visit_date,
        },
    )


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