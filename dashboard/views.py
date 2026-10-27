from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q, Sum,Count
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.views.decorators.http import require_POST
from decimal import Decimal

from appointments.models import Appointment, AppointmentStatus
from core.decorators import role_required
from accounts.choices import UserRole
from patients.models import Patient
from doctors.models import Doctor
from billing.models import Billing, Payment
from security_audit.models import AuditLog
from security_audit.services import log_security_event

User = get_user_model()

MANAGED_ROLES = [
    UserRole.PATIENT,
    UserRole.DOCTOR,
    UserRole.RECEPTIONIST,
]


def get_profile_urls(user):
    """
    Return existing module URLs for a user's profile.
    No duplicate edit/delete logic is created here.
    """
    try:
        if user.role == UserRole.PATIENT:
            profile = user.patient_profile
            namespace = "patients"
            detail = "detail"
            edit = "update"
            delete = "delete"

        elif user.role == UserRole.DOCTOR:
            profile = user.doctor_profile
            namespace = "doctors"
            detail = "detail"
            edit = "update"
            delete = "delete"

        elif user.role == UserRole.RECEPTIONIST:
            profile = user.receptionist_profile
            namespace = "receptionist"
            detail = "detail"
            edit = "update"
            delete = "delete"

        else:
            return None

    except ObjectDoesNotExist:
        # Account exists but its role-specific profile is missing.
        return None

    pk = profile.pk

    return {
        "detail_url": reverse(
            f"{namespace}:{detail}", args=[pk]
        ),
        "edit_url": reverse(
            f"{namespace}:{edit}", args=[pk]
        ),
        "delete_url": reverse(
            f"{namespace}:{delete}", args=[pk]
        ),
    }


@role_required(UserRole.ADMIN)
def account_list(request):
    query = request.GET.get("q", "").strip()
    selected_role = request.GET.get("role", "").strip()
    selected_status = request.GET.get("status", "").strip()

    accounts = User.objects.filter(
        role__in=MANAGED_ROLES
    ).order_by("role", "first_name", "last_name")

    if query:
        accounts = accounts.filter(
            Q(username__icontains=query)
            | Q(first_name__icontains=query)
            | Q(last_name__icontains=query)
            | Q(email__icontains=query)
            | Q(phone_number__icontains=query)
        )

    valid_roles = {role for role in MANAGED_ROLES}

    if selected_role in valid_roles:
        accounts = accounts.filter(role=selected_role)
    else:
        selected_role = ""

    if selected_status == "active":
        accounts = accounts.filter(is_active=True)
    elif selected_status == "inactive":
        accounts = accounts.filter(is_active=False)
    else:
        selected_status = ""

    paginator = Paginator(accounts, 10)
    page_obj = paginator.get_page(request.GET.get("page"))

    # Attach URLs to each account for the template.
    for account in page_obj.object_list:
        account.profile_urls = get_profile_urls(account)

    context = {
        "page_obj": page_obj,
        "query": query,
        "selected_role": selected_role,
        "selected_status": selected_status,
        "role_choices": [
            (UserRole.PATIENT, "Patient"),
            (UserRole.DOCTOR, "Doctor"),
            (UserRole.RECEPTIONIST, "Receptionist"),
        ],
        "total_accounts": User.objects.filter(
            role__in=MANAGED_ROLES
        ).count(),
        "active_accounts": User.objects.filter(
            role__in=MANAGED_ROLES,
            is_active=True,
        ).count(),
        "inactive_accounts": User.objects.filter(
            role__in=MANAGED_ROLES,
            is_active=False,
        ).count(),
    }

    return render(
        request,
        "dashboard/accounts.html",
        context,
    )


@role_required(UserRole.ADMIN)
@require_POST
def toggle_account_status(request, pk):
    # Only Patient, Doctor and Receptionist accounts are managed here.
    account = get_object_or_404(
        User,
        pk=pk,
        role__in=MANAGED_ROLES,
    )

    # Prevent an administrator from disabling their own login
    # through this endpoint.
    if account.pk == request.user.pk:
        messages.error(
            request,
            "You cannot deactivate your own account here.",
        )
        return redirect("dashboard:accounts")

    account.is_active = not account.is_active
    account.save(update_fields=["is_active"])
    log_security_event(
        request,
        action=(
            "ACCOUNT_ACTIVATED"
            if account.is_active
            else "ACCOUNT_DEACTIVATED"
        ),
        outcome=AuditLog.Outcome.SUCCESS,
        target_user=account,
    )

    status = "activated" if account.is_active else "deactivated"

    messages.success(
        request,
        f"{account.get_full_name() or account.username} "
        f"account {status} successfully.",
    )

    return redirect("dashboard:accounts")


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
    
    if request.user.role == UserRole.RECEPTIONIST:
        return redirect("receptionist:dashboard")   

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
    total_doctors = Doctor.objects.count()

    total_revenue = (
        Payment.objects.aggregate(
            total=Sum("amount")
        )["total"]
        or Decimal("0.00")
    )

    total_billed = (
        Billing.objects.aggregate(
            total=Sum("total_amount")
        )["total"]
        or Decimal("0.00")
    )

    pending_confirmations = Appointment.objects.filter(
        appointment_date=today,
        status=AppointmentStatus.SCHEDULED,
    ).count()

     # --------------------------------------------------
    # Appointment Status Chart: database-driven values
    # --------------------------------------------------

    # Independent of the appointment table's search/date/status filters.
    status_counts = {
        item["status"]: item["total"]
        for item in Appointment.objects.values("status").annotate(
            total=Count("id")
        )
    }

    completed_appointments = status_counts.get(
        AppointmentStatus.COMPLETED, 0
    )

    cancelled_appointments = status_counts.get(
        AppointmentStatus.CANCELLED, 0
    )

    # Scheduled and Confirmed appointments are grouped as Waiting.
    waiting_appointments = (
        status_counts.get(AppointmentStatus.SCHEDULED, 0)
        + status_counts.get(AppointmentStatus.CONFIRMED, 0)
    )

    total_status_appointments = (
        completed_appointments
        + waiting_appointments
        + cancelled_appointments
    )

    def percentage(count, total):
        return round((count * 100 / total), 1) if total else 0

    completed_percentage = percentage(
        completed_appointments,
        total_status_appointments,
    )

    waiting_percentage = percentage(
        waiting_appointments,
        total_status_appointments,
    )

    cancelled_percentage = percentage(
        cancelled_appointments,
        total_status_appointments,
    )

    # SVG dash offsets position each segment after the previous one.
    completed_remainder = 100 - completed_percentage
    waiting_remainder = 100 - waiting_percentage
    cancelled_remainder = 100 - cancelled_percentage

    waiting_offset = -completed_percentage
    cancelled_offset = -(
        completed_percentage + waiting_percentage
    )

    context = {
        "total_patients": total_patients,
        "total_doctors": total_doctors,
        "total_appointments": today_appointments,
        "total_revenue": total_revenue,
        "total_billed": total_billed,
        "pending_confirmations": pending_confirmations,
        "page_obj": page_obj,
        "search": search,
        "status": status,
        "date": date,
        "status_choices": AppointmentStatus.choices,

        # Appointment Status chart values
        "total_status_appointments": total_status_appointments,
        "completed_appointments": completed_appointments,
        "waiting_appointments": waiting_appointments,
        "cancelled_appointments": cancelled_appointments,
        "completed_percentage": completed_percentage,
        "waiting_percentage": waiting_percentage,
        "cancelled_percentage": cancelled_percentage,
        "completed_remainder": completed_remainder,
        "waiting_remainder": waiting_remainder,
        "cancelled_remainder": cancelled_remainder,
        "waiting_offset": waiting_offset,
        "cancelled_offset": cancelled_offset,
    }


    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )