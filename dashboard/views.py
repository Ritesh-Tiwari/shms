from django.shortcuts import get_object_or_404, render
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q

from appointments.models import Appointment, AppointmentStatus
from core.decorators import role_required
from accounts.choices import UserRole
from patients.models import Patient


# Create your views here.

@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
)
def dashboard(request):
    
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

    today = timezone.localdate()

    appointments = Appointment.objects.select_related(
        "patient__user",
        "doctor__user",
    ).filter(
        appointment_date=today,
    ).order_by(
        "appointment_time",
    )

    today_appointments = appointments.count()

    total_patients = Patient.objects.count()

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

    



    context = {

        "total_patients": total_patients,
        "total_doctors": 20,
        "total_appointments": today_appointments,
        "total_revenue": 20000,
        "page_obj": page_obj,
        "search": search,
        "status_choices": AppointmentStatus.choices,

    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )