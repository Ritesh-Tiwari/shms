from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import IntegrityError
from datetime import date
from core.decorators import role_required
from accounts.choices import UserRole
from .models import Appointment, AppointmentStatus
from .forms import AppointmentForm, AppointmentUpdateForm, PatientAppointmentForm
from .services import AppointmentService


@role_required(
    UserRole.ADMIN,
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
)
def appointment_list(request):

    search = request.GET.get(
        "search",
        "",
    ).strip()

    status = request.GET.get(
        "status",
        "",
    ).strip()

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
            "status_choices": AppointmentStatus.choices,
        },
    )


@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
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
    UserRole.ADMIN,
    UserRole.DOCTOR,
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

    if request.method == "POST":

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