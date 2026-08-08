from django.contrib import messages
from django.shortcuts import redirect, render
from django.core.paginator import Paginator

from core.decorators import role_required
from accounts.choices import UserRole
from .models import Appointment
from .forms import AppointmentForm
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