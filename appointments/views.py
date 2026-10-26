from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import IntegrityError
from datetime import date,timedelta
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils.dateparse import parse_date
from django.views.decorators.http import require_GET

from core.decorators import role_required
from accounts.choices import UserRole
from .models import Appointment, AppointmentStatus
from .forms import AppointmentForm, AppointmentUpdateForm, PatientAppointmentForm
from .services import AppointmentService
from doctors.models import Doctor
from .availability import (
    get_available_dates,
    get_available_slots,
)


@role_required(
    UserRole.ADMIN,
    UserRole.RECEPTIONIST,
)
def create_appointment(request):

    if request.method == "POST":

        form = AppointmentForm(request.POST)

        if form.is_valid():

            try:

                AppointmentService.create_appointment(
                    appointment_data=form.cleaned_data,
                )

                messages.success(
                    request,
                    "Appointment created successfully.",
                )

                return redirect(
                    "appointments:list",
                )

            except ValueError as error:

                form.add_error(
                    None,
                    str(error),
                )

    else:

        form = AppointmentForm()

    return render(
        request,
        "appointments/create.html",
        {
            "form": form,
        },
    )

@role_required(
    UserRole.PATIENT,
)
def my_appointments(request):

    appointments = (
        Appointment.objects
        .select_related(
            "patient__user",
            "doctor__user",
        )
        .filter(
            patient__user=request.user,
        )
        .order_by(
            "-appointment_date",
        )
    )
    # Target counts according to status or date
    upcoming_count = appointments.filter(
        status__in=['SCHEDULED', 'CONFIRMED', 'PENDING'],
        appointment_date__gte=date.today()
    ).count()

    past_count = appointments.filter(
        status__in=['COMPLETED', 'CANCELLED']
    ).count() # ya appointment_date__lt=timezone.now().date()
    
    all_count = appointments.count()
    paginator = Paginator(
        appointments,
        10,
    )

    page_number = request.GET.get(
        "page",
    )

    page_obj = paginator.get_page(
        page_number,
    )

    return render(
        request,
        "appointments/my_appointments.html",
        {
            "page_obj": page_obj,
            'upcoming_count': upcoming_count,
            'past_count': past_count,
            'all_count': all_count,
        },
    )

@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.RECEPTIONIST,
)
def appointment_list(request):
    doctor_id = request.GET.get('doctor')

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()
    if status == "all":
        status = ""

    date = request.GET.get(
        "date",
        "",
    ).strip()

    appointments = Appointment.objects.select_related(
        "patient__user",
        "doctor__user",
    )

    # Doctor → only their own appointments
    if request.user.role == UserRole.DOCTOR:
        appointments = appointments.filter(
            doctor__user=request.user,
        )

    # Search
    if search:

        appointments = appointments.filter(

            Q(appointment_id__icontains=search)

            | Q(
                patient__user__first_name__icontains=search
            )

            | Q(
                patient__user__last_name__icontains=search
            )

            | Q(
                doctor__user__first_name__icontains=search
            )

            | Q(
                doctor__user__last_name__icontains=search
            )

        )

    # Status filter
    if status:

        appointments = appointments.filter(
            status=status,
        )

    # Date filter
    if date:

        appointments = appointments.filter(
            appointment_date=date,
        )

    paginator = Paginator(
        appointments,
        10,
    )

    page_number = request.GET.get(
        "page",
    )

    page_obj = paginator.get_page(
        page_number,
    )

    return render(
        request,
        "appointments/list.html",
        {
            "page_obj": page_obj,
            "search": search,
            "status": status,
            "date": date,
            "doctor_id":doctor_id,
            "status_choices": AppointmentStatus.choices,
        },
    )


@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.RECEPTIONIST
)
def appointment_detail(request, pk):

    appointments = Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
            "billing",
        )

    if request.user.role == UserRole.DOCTOR:
        appointments = appointments.filter(
            doctor__user=request.user,
        )

    appointment = get_object_or_404(
        appointments,
        pk=pk,
    )

    billing = getattr(
        appointment,
        "billing",
        None,
    )

    return render(
        request,
        "appointments/detail.html",
        {
            "appointment": appointment,
            "billing": billing,
        },
    )

@role_required(
    UserRole.PATIENT,
)
def my_appointment_detail(request, pk):

    appointments = (
        Appointment.objects
        .select_related(
            "patient__user",
            "doctor__user",
        )
        .filter(
            patient__user=request.user,
        )
    )

    appointment = get_object_or_404(
        appointments,
        pk=pk,
    )

    return render(
        request,
        "appointments/my_detail.html",
        {
            "appointment": appointment,
        },
    )


@role_required(
    UserRole.ADMIN,
    UserRole.RECEPTIONIST
)
def update_appointment(request, pk):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
        ),
        pk=pk,
    )

    if request.method == "POST":

        form = AppointmentUpdateForm(
            request.POST,
            instance=appointment,
        )

        if form.is_valid():

            try:

                AppointmentService.update_appointment(
                    appointment=appointment,
                    appointment_data=form.cleaned_data,
                )

                messages.success(
                    request,
                    "Appointment updated successfully.",
                )

                return redirect(
                    "appointments:detail",
                    pk=appointment.pk,
                )

            except ValueError as error:

                form.add_error(
                    None,
                    str(error),
                )

    else:

        form = AppointmentUpdateForm(
            instance=appointment,
        )

    return render(
        request,
        "appointments/update.html",
        {
            "form": form,
            "appointment": appointment,
        },
    )

@role_required(
    UserRole.PATIENT,
)
def my_reschedule_appointment(request, pk):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
        ),
        pk=pk,
        patient__user=request.user,
    )

    if appointment.status in ['COMPLETED', 'CANCELLED']:
        messages.error(request, "You cannot reschedule a completed or cancelled appointment.")
        return redirect("dashboard:dashboard")
    
    if request.method == "POST":

        form = AppointmentUpdateForm(
            request.POST,
            instance=appointment,
        )

        if form.is_valid():

            try:

                AppointmentService.update_appointment(
                    appointment=appointment,
                    appointment_data=form.cleaned_data,
                )

                messages.success(
                    request,
                    "Appointment updated successfully.",
                )

                return redirect(
                    "appointments:my-appointment-detail",
                    pk=appointment.pk,
                )

            except ValueError as error:

                form.add_error(
                    None,
                    str(error),
                )

    else:

        form = AppointmentUpdateForm(
            instance=appointment,
        )

    tomorrow = date.today() + timedelta(days=1)

    return render(
        request,
        "appointments/my_reschedule.html",
        {
            "form": form,
            "appointment": appointment,
            "tomorrow_date":tomorrow.strftime("%Y-%m-%d"),
        },
    )

@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.RECEPTIONIST
)
def cancel_appointment(request, pk):

    appointments = Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
        )

    if request.user.role == UserRole.DOCTOR:
        appointments = appointments.filter(
            doctor__user=request.user,
        )

    appointment = get_object_or_404(
        appointments,
        pk=pk,
    )

    if request.method == "POST":

        try:

            AppointmentService.cancel_appointment(
                appointment=appointment,
            )

            messages.success(
                request,
                "Appointment cancelled successfully.",
            )

            return redirect(
                "appointments:detail",
                pk=appointment.pk,
            )

        except ValueError as error:

            messages.error(
                request,
                str(error),
            )

            return redirect(
                "appointments:detail",
                pk=appointment.pk,
            )

    return render(
        request,
        "appointments/cancel.html",
        {
            "appointment": appointment,
        },
    )


@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.RECEPTIONIST
)
def update_appointment_status(request, pk):

    appointments = Appointment.objects.select_related(
        "patient__user",
        "doctor__user",
    )

    # Doctor can update status only for their own appointments
    if request.user.role == UserRole.DOCTOR:
        appointments = appointments.filter(
            doctor__user=request.user,
        )

    appointment = get_object_or_404(
        appointments,
        pk=pk,
    )


    if request.method != "POST":
        messages.error(
            request,
            "Invalid request method.",
        )
        return redirect(
            "appointments:detail",
            pk=appointment.pk,
        )

    new_status = request.POST.get("status")

    try:

        AppointmentService.update_status(
            appointment=appointment,
            new_status=new_status,
        )

        messages.success(
            request,
            "Appointment status updated successfully.",
        )   

    except ValueError as error:

        messages.error(
            request,
            str(error),
        )

    return redirect(
        "appointments:detail",
        pk=appointment.pk,
    )


@role_required(
    UserRole.PATIENT,
)
def book_appointment(request):

    patient = getattr(
        request.user,
        "patient_profile",
        None,
    )

    if patient is None:

        messages.error(
            request,
            "Patient profile not found.",
        )

        return redirect(
            "dashboard:dashboard",
        )

    if request.method == "POST":

        form = PatientAppointmentForm(
            request.POST,
        )

        if form.is_valid():

            try:

                AppointmentService.create_appointment(
                    appointment_data={
                        "patient": patient,
                        "doctor": form.cleaned_data["doctor"],
                        "appointment_date": form.cleaned_data[
                            "appointment_date"
                        ],
                        "appointment_time": form.cleaned_data[
                            "appointment_time"
                        ],
                        "reason_for_visit": form.cleaned_data[
                            "reason_for_visit"
                        ],
                    },
                )

                messages.success(
                    request,
                    "Appointment request submitted successfully.",
                )

                return redirect(
                    "appointments:my-appointments",
                )

            except ValueError as error:

                form.add_error(
                    None,
                    str(error),
                )

            except IntegrityError:

                form.add_error(
                    None,
                    "The selected appointment slot is no longer available.",
                )

    else:

        form = PatientAppointmentForm()

    return render(
        request,
        "appointments/book.html",
        {
            "form": form,
            "patient": patient,
        },
    )



@role_required(
    UserRole.PATIENT,
)
def my_cancel_appointment(request, pk):

    appointments = (
        Appointment.objects
        .filter(
            patient__user=request.user,
        )
    )

    appointment = get_object_or_404(
        appointments,
        pk=pk,
    )

    if request.method == "POST":

        try:

            AppointmentService.cancel_appointment(
                appointment=appointment,
            )

            messages.success(
                request,
                "Appointment cancelled successfully.",
            )

        except ValueError as error:

            messages.error(
                request,
                str(error),
            )

        return redirect(
            "appointments:my-appointment-detail",
            pk=appointment.pk,
        )

    return render(
        request,
        "appointments/my_cancel.html",
        {
            "appointment": appointment,
        },
    )


@login_required
@require_GET
def available_dates_api(request):

    doctor_id = request.GET.get("doctor_id")

    if not doctor_id:
        return JsonResponse(
            {
                "dates": [],
                "message": "Please select a doctor first.",
            },
            status=400,
        )

    doctor = get_object_or_404(
        Doctor.objects.select_related("user"),
        pk=doctor_id,
    )

    available_dates = get_available_dates(doctor)

    return JsonResponse(
        {
            "dates": [
                {
                    "value": available_date.isoformat(),
                    "label": available_date.strftime(
                        "%a, %d %b %Y"
                    ),
                }
                for available_date in available_dates
            ],
        }
    )


@login_required
@require_GET
def available_times_api(request):

    doctor_id = request.GET.get("doctor_id")
    selected_date = parse_date(
        request.GET.get("date", "")
    )
    exclude_appointment_id = request.GET.get(
        "exclude_appointment_id"
    )

    if not doctor_id or not selected_date:
        return JsonResponse(
            {
                "times": [],
                "message": "Select a doctor and date.",
            },
            status=400,
        )

    doctor = get_object_or_404(
        Doctor.objects.select_related("user"),
        pk=doctor_id,
    )

    available_slots = get_available_slots(
        doctor=doctor,
        appointment_date=selected_date,
        exclude_appointment_id=exclude_appointment_id,
    )

    return JsonResponse(
        {
            "times": [
                {
                    "value": slot.strftime("%H:%M"),
                    "label": slot.strftime("%I:%M %p"),
                }
                for slot in available_slots
            ],
        }
    )