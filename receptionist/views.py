from django.contrib import messages
from django.db import IntegrityError
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import (
    get_object_or_404,
    redirect,
    render,
)
from django.views.decorators.http import (
    require_POST,require_http_methods,
)
from django.utils import timezone
import logging


from accounts.choices import UserRole
from appointments.models import (
    Appointment,
    AppointmentStatus,
)
from core.decorators import role_required
from patients.models import Patient

from .forms import AppointmentSearchForm, ReceptionistProfileForm, ReceptionistUserForm
from .services import ReceptionistService
from .models import Receptionist


@role_required(UserRole.ADMIN)
def receptionist_list(request):

    query = request.GET.get(
        "q",
        "",
    ).strip()

    receptionists = (
        Receptionist.objects
        .select_related("user")
    )

    if query:

        receptionists = receptionists.filter(

            Q(receptionist_id__icontains=query)

            | Q(
                user__first_name__icontains=query
            )

            | Q(
                user__last_name__icontains=query
            )

            | Q(
                user__email__icontains=query
            )

            | Q(
                user__phone_number__icontains=query
            )

            | Q(
                user__username__icontains=query
            )
        )

    paginator = Paginator(
        receptionists,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page")
    )

    return render(
        request,
        "receptionist/list.html",
        {
            "page_obj": page_obj,
            "query": query,
        },
    )


@role_required(UserRole.ADMIN)
def create_receptionist(request):
    logger = logging.getLogger(__name__)

    if request.method == "POST":

        user_form = ReceptionistUserForm(
            request.POST,
        )

        profile_form = ReceptionistProfileForm(
            request.POST,
        )

        user_valid = user_form.is_valid()

        profile_valid = profile_form.is_valid()

        if user_valid and profile_valid:

            try:

                receptionist = (
                    ReceptionistService.create_receptionist(

                        user_data=user_form.cleaned_data,

                        profile_data=profile_form.cleaned_data,
                    )
                )

            except IntegrityError:

                logger.exception(
                    "Receptionist creation failed due to IntegrityError"
                )
                user_form.add_error(
                    None,
                    (
                        "Unable to create receptionist. "
                        "The username or email may already "
                        "be registered."
                    ),
                )

            else:

                messages.success(
                    request,
                    (
                        "Receptionist account created "
                        "successfully."
                    ),
                )

                return redirect(
                    "receptionist:detail",
                    pk=receptionist.pk,
                )

    else:

        user_form = ReceptionistUserForm()

        profile_form = ReceptionistProfileForm()

    return render(
        request,
        "receptionist/form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "page_title": "Create Receptionist",
            "button_text": "Create Receptionist",
        },
    )


@role_required(UserRole.ADMIN)
def receptionist_detail(request, pk):

    receptionist = get_object_or_404(

        Receptionist.objects.select_related("user"),

        pk=pk,
    )

    return render(
        request,
        "receptionist/detail.html",
        {
            "receptionist": receptionist,
        },
    )


@role_required(UserRole.ADMIN)
def update_receptionist(request, pk):

    receptionist = get_object_or_404(

        Receptionist.objects.select_related("user"),

        pk=pk,
    )

    if request.method == "POST":

        user_form = ReceptionistUserForm(

            request.POST,

            instance=receptionist.user,
        )

        profile_form = ReceptionistProfileForm(

            request.POST,

            instance=receptionist,
        )

        user_valid = user_form.is_valid()

        profile_valid = profile_form.is_valid()

        if user_valid and profile_valid:

            try:

                receptionist = (
                    ReceptionistService.update_receptionist(

                        receptionist=receptionist,

                        user_data=user_form.cleaned_data,

                        profile_data=profile_form.cleaned_data,
                    )
                )

            except IntegrityError:

                user_form.add_error(
                    None,
                    (
                        "Unable to update receptionist. "
                        "The username or email may already "
                        "be registered."
                    ),
                )

            else:

                messages.success(
                    request,
                    "Receptionist updated successfully.",
                )

                return redirect(
                    "receptionist:detail",
                    pk=receptionist.pk,
                )

    else:

        user_form = ReceptionistUserForm(

            instance=receptionist.user,
        )

        profile_form = ReceptionistProfileForm(

            instance=receptionist,
        )

    return render(
        request,
        "receptionist/form.html",
        {
            "user_form": user_form,
            "profile_form": profile_form,
            "receptionist": receptionist,
            "page_title": "Update Receptionist",
            "button_text": "Save Changes",
        },
    )


@role_required(UserRole.ADMIN)
@require_http_methods(["GET", "POST"])
def delete_receptionist(request, pk):

    receptionist = get_object_or_404(

        Receptionist.objects.select_related("user"),

        pk=pk,
    )

    if request.method == "POST":

        try:

            ReceptionistService.delete_receptionist(

                receptionist=receptionist,
            )

        except IntegrityError:

            messages.error(
                request,
                (
                    "Unable to delete receptionist. "
                    "Please check related records."
                ),
            )

            return redirect(
                "receptionist:detail",
                pk=pk,
            )

        messages.success(
            request,
            "Receptionist account deleted successfully.",
        )

        return redirect(
            "receptionist:list",
        )

    return render(
        request,
        "receptionist/delete.html",
        {
            "receptionist": receptionist,
        },
    )


@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def dashboard(request):

    today = timezone.localdate()
    # today = __import__(
    #     "django.utils.timezone",
    #     fromlist=["localdate"],
    # ).localdate()

    appointments = Appointment.objects.filter(
        appointment_date=today,
    )

    context = {
        "total_patients": Patient.objects.count(),
        "today_appointments": appointments.count(),

        "scheduled_count": appointments.filter(
            status=AppointmentStatus.SCHEDULED,
        ).count(),

        "confirmed_count": appointments.filter(
            status=AppointmentStatus.CONFIRMED,
        ).count(),

        "checked_in_count": appointments.filter(
            checked_in_at__isnull=False,
        ).count(),

        "completed_count": appointments.filter(
            status=AppointmentStatus.COMPLETED,
        ).count(),

        "appointments": (
            appointments
            .select_related(
                "patient__user",
                "doctor__user",
            )
            .order_by("appointment_time")
        ),
    }

    return render(
        request,
        "receptionist/dashboard.html",
        context,
    )


@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
def appointment_list(request):

    form = AppointmentSearchForm(
        request.GET or None,
    )

    appointments = (
        Appointment.objects
        .select_related(
            "patient__user",
            "doctor__user",
        )
    )

    if form.is_valid():

        search = form.cleaned_data.get(
            "search",
            "",
        )

        appointment_date = (
            form.cleaned_data.get(
                "appointment_date",
            )
        )

        status = form.cleaned_data.get(
            "status",
            "",
        )

        if search:
            appointments = appointments.filter(
                Q(appointment_id__icontains=search)
                | Q(
                    patient__patient_id__icontains=search
                )
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

        if appointment_date:
            appointments = appointments.filter(
                appointment_date=appointment_date,
            )

        if status:
            appointments = appointments.filter(
                status=status,
            )

    appointments = appointments.order_by(
        "appointment_date",
        "appointment_time",
    )

    paginator = Paginator(
        appointments,
        10,
    )

    page_obj = paginator.get_page(
        request.GET.get("page"),
    )

    return render(
        request,
        "receptionist/appointments.html",
        {
            "form": form,
            "page_obj": page_obj,
        },
    )


@role_required(UserRole.ADMIN, UserRole.RECEPTIONIST)
@require_POST
def check_in(request, pk):

    appointment = get_object_or_404(
        Appointment,
        pk=pk,
    )

    try:

        ReceptionistService.check_in_appointment(
            appointment_id=appointment.pk,
        )

    except ValidationError as error:

        messages.error(
            request,
            " ".join(error.messages),
        )

        return redirect(
            "receptionist:appointments",
        )

    messages.success(
        request,
        (
            f"Patient check-in recorded for "
            f"{appointment.appointment_id}."
        ),
    )

    return redirect(
        "receptionist:appointments",
    )