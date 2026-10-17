from django.shortcuts import get_object_or_404, render, redirect
from django.core.paginator import Paginator
from django.utils import timezone
from django.db.models import Q
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from django.views.decorators.http import require_POST

from appointments.models import Appointment, AppointmentStatus
from core.decorators import role_required
from accounts.choices import UserRole
from patients.models import Patient


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