from django.contrib import messages
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone


from accounts.forms import UserRegistrationForm
from .forms import DoctorForm, DoctorScheduleForm
from .services import DoctorService
from .models import Doctor, DoctorSchedule
from .choices import AvailabilityChoices, SpecializationChoices
from core.decorators import role_required
from accounts.choices import UserRole
from appointments.models import Appointment, AppointmentStatus
from prescriptions.models import Prescription
from patients.models import Patient

@role_required(UserRole.DOCTOR)
def doctor_dashboard(request):
    today = timezone.localdate()

    doctor = get_object_or_404(
        Doctor.objects.select_related("user"),
        user=request.user,
    )

    appointments = (
        Appointment.objects
        .filter(doctor=doctor)
        .select_related("patient__user")
        .order_by("appointment_date", "appointment_time")
    )

    today_appointments = appointments.filter(
        appointment_date=today
    )

    context = {
        "doctor": doctor,
        "today": today,
        "today_appointments": today_appointments,
        "today_count": today_appointments.count(),
        "upcoming_count": appointments.filter(
            appointment_date__gt=today,
            status__in=[
                AppointmentStatus.SCHEDULED,
                AppointmentStatus.CONFIRMED,
            ],
        ).count(),
        "completed_count": appointments.filter(
            status=AppointmentStatus.COMPLETED,
        ).count(),
        "cancelled_count": appointments.filter(
            status=AppointmentStatus.CANCELLED,
        ).count(),
        "prescription_count": Prescription.objects.filter(
            appointment__doctor=doctor,
        ).count(),
        "patient_count": appointments.values(
            "patient_id"
        ).distinct().count(),
    }

    return render(
        request,
        "doctors/dashboard.html",
        context,
    )


@role_required(
    UserRole.ADMIN,
)
def register_doctor(request):

    if request.method == "POST":

        user_form = UserRegistrationForm(request.POST)

        doctor_form = DoctorForm(request.POST)

        if user_form.is_valid() and doctor_form.is_valid():

            DoctorService.create_doctor(

                user_data=user_form.cleaned_data,

                doctor_data=doctor_form.cleaned_data,

            )

            messages.success(
                request,
                "Doctor registered successfully.",
            )

            return redirect("doctors:list")
        
    else:

        user_form = UserRegistrationForm()

        doctor_form = DoctorForm()

    return render(
        request,
        "doctors/register.html",
        {
            "user_form": user_form,
            "doctor_form": doctor_form,
        },
    )

@role_required(
    UserRole.ADMIN,
)
def doctor_list(request):

    search = request.GET.get("search", "").strip()
    specialization = request.GET.get("specialization", "").strip()
    availability = request.GET.get("availability", "").strip()

    doctors = Doctor.objects.select_related("user")

    if search:

        doctors = doctors.filter(

            Q(doctor_id__icontains=search)

            | Q(user__first_name__icontains=search)

            | Q(user__last_name__icontains=search)

            | Q(user__email__icontains=search)
        )

    valid_specializations = {
        value for value, label in SpecializationChoices.choices
    }

    valid_availability = {
        value for value, label in AvailabilityChoices.choices
    }

    if specialization in valid_specializations:
        doctors = doctors.filter(
            specialization=specialization,
        )

    if availability in valid_availability:
        doctors = doctors.filter(
            availability=availability,
        )

    paginator = Paginator(doctors, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    return render(
        request,
        "doctors/list.html",
        {
            "page_obj": page_obj,
            "search": search,
            "specialization": specialization,
            "availability": availability,
            "specialization_choices": SpecializationChoices.choices,
            "availability_choices": AvailabilityChoices.choices,
        },
    )

@role_required(
    UserRole.ADMIN,
)
def doctor_detail(request, pk):

    doctor = get_object_or_404(
        Doctor.objects.select_related("user"),
        pk=pk,
    )

    return render(
        request,
        "doctors/detail.html",
        {
            "doctor": doctor,
        },
    )

@role_required(
    UserRole.ADMIN,
)
def update_doctor(request, pk):

    doctor = get_object_or_404(
        Doctor,
        pk=pk,
    )

    if request.method == "POST":

        user_form = UserRegistrationForm(
            request.POST,
            instance=doctor.user,
        )

        doctor_form = DoctorForm(
            request.POST,
            instance=doctor,
        )

        if user_form.is_valid() and doctor_form.is_valid():

            DoctorService.update_doctor(
                doctor=doctor,
                user_data=user_form.cleaned_data,
                doctor_data=doctor_form.cleaned_data,
            )

            messages.success(
                request,
                "Doctor updated successfully.",
            )

            return redirect(
                "doctors:detail",
                doctor.pk,
            )

    else:

        user_form = UserRegistrationForm(
            instance=doctor.user,
        )

        doctor_form = DoctorForm(
            instance=doctor,
        )

    return render(
        request,
        "doctors/update.html",
        {
            "user_form": user_form,
            "doctor_form": doctor_form,
            "doctor": doctor,
        },
    )

@role_required(
    UserRole.ADMIN,
)
def delete_doctor(request, pk):

    doctor = get_object_or_404(
        Doctor,
        pk=pk,
    )

    if request.method == "POST":

        doctor.user.delete()

        messages.success(
            request,
            "Doctor deleted successfully.",
        )

        return redirect(
            "doctors:list",
        )

    return render(
        request,
        "doctors/delete.html",
        {
            "doctor": doctor,
        },
    )


@role_required(UserRole.ADMIN)
def toggle_doctor_active(request, pk):
    doctor = get_object_or_404(
        Doctor.objects.select_related("user"),
        pk=pk,
    )

    if request.method != "POST":
        messages.error(
            request,
            "Use the form to change account status.",
        )
        return redirect(
            "doctors:detail",
            pk=doctor.pk,
        )

    doctor.user.is_active = not doctor.user.is_active
    doctor.user.save(update_fields=["is_active", "updated_at"])

    if doctor.user.is_active:
        messages.success(request, "Doctor account activated.")
    else:
        messages.success(request, "Doctor account deactivated.")

    return redirect(
        "doctors:detail",
        pk=doctor.pk,
    )

@role_required(UserRole.DOCTOR)
def my_schedule(request):
    doctor = get_object_or_404(
        Doctor,
        user=request.user,
    )

    schedules = DoctorSchedule.objects.filter(
        doctor=doctor,
    )

    return render(
        request,
        "doctors/schedule.html",
        {
            "doctor": doctor,
            "schedules": schedules,
        },
    )


@role_required(UserRole.DOCTOR)
def add_schedule(request):
    doctor = get_object_or_404(
        Doctor,
        user=request.user,
    )

    if request.method == "POST":
        form = DoctorScheduleForm(request.POST)

        if form.is_valid():
            schedule = form.save(commit=False)
            schedule.doctor = doctor

            try:
                schedule.full_clean()
                schedule.save()

                messages.success(
                    request,
                    "Schedule added successfully.",
                )

                return redirect("doctors:schedule")

            except Exception:
                form.add_error(
                    None,
                    "Could not save schedule. "
                    "Check for duplicate or invalid times.",
                )
    else:
        form = DoctorScheduleForm()

    return render(
        request,
        "doctors/schedule_form.html",
        {
            "form": form,
        },
    )


@role_required(UserRole.DOCTOR)
def delete_schedule(request, pk):
    doctor = get_object_or_404(
        Doctor,
        user=request.user,
    )

    schedule = get_object_or_404(
        DoctorSchedule,
        pk=pk,
        doctor=doctor,
    )

    if request.method == "POST":
        schedule.delete()

        messages.success(
            request,
            "Schedule deleted successfully.",
        )

        return redirect("doctors:schedule")

    return render(
        request,
        "doctors/schedule_delete.html",
        {
            "schedule": schedule,
        },
    )

@role_required(UserRole.DOCTOR)
def my_patients(request):
    doctor = get_object_or_404(
        Doctor,
        user=request.user,
    )

    search = request.GET.get("search", "").strip()

    patients = (
        Patient.objects
        .filter(appointments__doctor=doctor)
        .select_related("user")
        .distinct()
        .order_by("user__first_name", "user__last_name")
    )

    if search:
        patients = patients.filter(
            Q(patient_id__icontains=search)
            | Q(user__first_name__icontains=search)
            | Q(user__last_name__icontains=search)
            | Q(user__email__icontains=search)
        )

    page_obj = Paginator(patients, 10).get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "doctors/my_patients.html",
        {
            "page_obj": page_obj,
            "search": search,
        },
    )


@role_required(UserRole.DOCTOR)
def patient_clinical_summary(request, pk):
    doctor = get_object_or_404(
        Doctor,
        user=request.user,
    )

    patient = get_object_or_404(
        Patient.objects.select_related("user"),
        pk=pk,
        appointments__doctor=doctor,
    )

    appointments = (
        Appointment.objects
        .filter(
            doctor=doctor,
            patient=patient,
        )
        .order_by("-appointment_date", "-appointment_time")
    )

    prescriptions = (
        Prescription.objects
        .filter(appointment__in=appointments)
        .prefetch_related("medicines")
        .order_by("-created_at")
    )

    return render(
        request,
        "doctors/patient_summary.html",
        {
            "patient": patient,
            "appointments": appointments,
            "prescriptions": prescriptions,
        },
    )
