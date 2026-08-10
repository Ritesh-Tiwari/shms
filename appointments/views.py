from django.contrib import messages
from django.shortcuts import redirect, render, get_object_or_404
from django.core.paginator import Paginator

from core.decorators import role_required
from accounts.choices import UserRole
from .models import Appointment
from .forms import AppointmentForm, AppointmentUpdateForm
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
    UserRole.ADMIN,
)
def appointment_list(request):

    appointments = Appointment.objects.select_related(
        "patient__user",
        "doctor__user",
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
        },
    )



@role_required(
    UserRole.ADMIN,
)
def appointment_detail(request, pk):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
        ),
        pk=pk,
    )

    return render(
        request,
        "appointments/detail.html",
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
)
def cancel_appointment(request, pk):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
        ),
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