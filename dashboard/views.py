from django.shortcuts import get_object_or_404, render, redirect
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
    UserRole.PATIENT,
    UserRole.RECEPTIONIST,
)
def dashboard(request):

    if request.user.role == UserRole.PATIENT:
        return redirect("patients:home")
    
    if request.user.role == UserRole.DOCTOR:
            return redirect("doctors:dashboard")

    search = request.GET.get("search", "").strip()
    status = request.GET.get("status", "").strip()
    date = request.GET.get("date", "").strip()

    today = timezone.localdate()

    # Base QuerySet
    appointments = Appointment.objects.select_related(
        "patient__user",
        "doctor__user",
    )

    # 1. Role-based Authorization / Scoping (FIX)
    if request.user.role == UserRole.PATIENT:
        appointments = appointments.filter(
            patient__user=request.user,
        )
    elif request.user.role == UserRole.DOCTOR:
        appointments = appointments.filter(
            doctor__user=request.user,
        )
    # Admin ke liye saare appointments accessible rehenge

    # 2. Date Filter (If date query parameter passed, use it; else default to today)
    if date:
        appointments = appointments.filter(appointment_date=date)
    else:
        appointments = appointments.filter(appointment_date=today)

    # 3. Status Filter (FIX)
    if status:
        appointments = appointments.filter(status=status)

    appointments = appointments.order_by("appointment_time")

    today_appointments = appointments.count()
    total_patients = Patient.objects.count()

    # 4. Search Filter
    if search:
        appointments = appointments.filter(
            Q(appointment_id__icontains=search)
            | Q(patient__user__first_name__icontains=search)
            | Q(patient__user__last_name__icontains=search)
            | Q(doctor__user__first_name__icontains=search)
            | Q(doctor__user__last_name__icontains=search)
        )

    paginator = Paginator(
        appointments,
        10,
    )

    page_number = request.GET.get("page")
    page_obj = paginator.get_page(page_number)

    context = {
        "total_patients": total_patients,
        "total_doctors": 20,
        "total_appointments": today_appointments,
        "total_revenue": 20000,
        "page_obj": page_obj,
        "search": search,
        "status": status,
        "date": date,
        "status_choices": AppointmentStatus.choices,
    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )