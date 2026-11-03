from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import render
from django.urls import reverse
from django.utils.http import url_has_allowed_host_and_scheme

from accounts.choices import UserRole
from appointments.models import Appointment
from billing.models import Billing
from doctors.models import Doctor
from patients.models import Patient
from prescriptions.models import Prescription


@login_required
def global_search(request):
    query = request.GET.get("q", "").strip()[:100]
    results = []
    role = request.user.role
    requested_return_url = request.GET.get("next", "")
    return_url = (
        requested_return_url
        if url_has_allowed_host_and_scheme(
            requested_return_url,
            allowed_hosts={request.get_host()},
            require_https=request.is_secure(),
        )
        else reverse("dashboard:dashboard")
    )

    def add_results(queryset, category, get_title, get_subtitle, get_url):
        for item in queryset[:8]:
            results.append({
                "category": category,
                "title": get_title(item),
                "subtitle": get_subtitle(item),
                "url": get_url(item),
            })

    if query:
        if role in (UserRole.ADMIN, UserRole.RECEPTIONIST):
            patients = Patient.objects.select_related("user").filter(
                Q(patient_id__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__email__icontains=query)
                | Q(user__phone_number__icontains=query)
            ).order_by("patient_id")
            add_results(
                patients,
                "Patient",
                lambda patient: patient.user.get_full_name() or patient.user.email,
                lambda patient: patient.patient_id,
                lambda patient: reverse("patients:detail", args=[patient.pk]),
            )

            doctors = Doctor.objects.select_related("user").filter(
                Q(doctor_id__icontains=query)
                | Q(user__first_name__icontains=query)
                | Q(user__last_name__icontains=query)
                | Q(user__email__icontains=query)
                | Q(specialization__icontains=query)
            ).order_by("doctor_id")
            add_results(
                doctors,
                "Doctor",
                lambda doctor: doctor.user.get_full_name() or doctor.user.email,
                lambda doctor: f"{doctor.doctor_id} · {doctor.get_specialization_display()}",
                lambda doctor: reverse("doctors:detail", args=[doctor.pk]),
            )

        if role in (UserRole.ADMIN, UserRole.DOCTOR, UserRole.RECEPTIONIST):
            appointments = Appointment.objects.select_related(
                "patient__user",
                "doctor__user",
            )
            if role == UserRole.DOCTOR:
                appointments = appointments.filter(doctor__user=request.user)

            appointments = appointments.filter(
                Q(appointment_id__icontains=query)
                | Q(patient__patient_id__icontains=query)
                | Q(patient__user__first_name__icontains=query)
                | Q(patient__user__last_name__icontains=query)
                | Q(doctor__doctor_id__icontains=query)
                | Q(doctor__user__first_name__icontains=query)
                | Q(doctor__user__last_name__icontains=query)
            ).order_by("-appointment_date", "-appointment_time")
            add_results(
                appointments,
                "Appointment",
                lambda appointment: appointment.appointment_id,
                lambda appointment: (
                    f"{appointment.patient.user.get_full_name() or appointment.patient.user.email} · "
                    f"{appointment.appointment_date} · "
                    f"{appointment.doctor.user.get_full_name() or appointment.doctor.user.email}"
                ),
                lambda appointment: reverse(
                    "appointments:detail",
                    args=[appointment.pk],
                ),
            )

        if role in (UserRole.ADMIN, UserRole.DOCTOR):
            bills = Billing.objects.select_related(
                "patient__user",
                "appointment__doctor__user",
            )
            if role == UserRole.DOCTOR:
                bills = bills.filter(appointment__doctor__user=request.user)

            bills = bills.filter(
                Q(bill_id__icontains=query)
                | Q(patient__patient_id__icontains=query)
                | Q(patient__user__first_name__icontains=query)
                | Q(patient__user__last_name__icontains=query)
                | Q(appointment__appointment_id__icontains=query)
            ).order_by("-bill_date")
            add_results(
                bills,
                "Bill",
                lambda bill: bill.bill_id,
                lambda bill: (
                    f"{bill.patient.user.get_full_name() or bill.patient.user.email} · "
                    f"{bill.get_payment_status_display()}"
                ),
                lambda bill: reverse("billing:detail", args=[bill.pk]),
            )

        if role in (UserRole.ADMIN, UserRole.DOCTOR):
            prescriptions = Prescription.objects.select_related(
                "appointment__patient__user",
                "appointment__doctor__user",
            )
            if role == UserRole.DOCTOR:
                prescriptions = prescriptions.filter(
                    appointment__doctor__user=request.user,
                )

            prescriptions = prescriptions.filter(
                Q(prescription_id__icontains=query)
                | Q(appointment__patient__patient_id__icontains=query)
                | Q(appointment__patient__user__first_name__icontains=query)
                | Q(appointment__patient__user__last_name__icontains=query)
                | Q(diagnosis__icontains=query)
                | Q(medicines__medicine_name__icontains=query)
            ).distinct().order_by("-created_at")
            add_results(
                prescriptions,
                "Prescription",
                lambda prescription: prescription.prescription_id,
                lambda prescription: (
                    f"{prescription.appointment.patient.user.get_full_name() or prescription.appointment.patient.user.email} · "
                    f"{prescription.created_at:%b %d, %Y}"
                ),
                lambda prescription: reverse(
                    "prescriptions:detail",
                    args=[prescription.pk],
                ),
            )

        if role == UserRole.PATIENT:
            appointments = Appointment.objects.filter(
                patient__user=request.user,
            ).select_related("doctor__user", "patient__user").filter(
                Q(appointment_id__icontains=query)
                | Q(doctor__user__first_name__icontains=query)
                | Q(doctor__user__last_name__icontains=query)
            ).order_by("-appointment_date", "-appointment_time")
            add_results(
                appointments,
                "Appointment",
                lambda appointment: appointment.appointment_id,
                lambda appointment: (
                    f"{appointment.doctor.user.get_full_name() or appointment.doctor.user.email} · "
                    f"{appointment.appointment_date}"
                ),
                lambda appointment: reverse(
                    "appointments:my-appointment-detail",
                    args=[appointment.pk],
                ),
            )

            bills = Billing.objects.filter(
                patient__user=request.user,
            ).select_related("patient__user").filter(
                Q(bill_id__icontains=query)
                | Q(appointment__appointment_id__icontains=query)
                | Q(payment_status__icontains=query)
            ).order_by("-bill_date")
            add_results(
                bills,
                "Bill",
                lambda bill: bill.bill_id,
                lambda bill: bill.get_payment_status_display(),
                lambda bill: reverse("billing:my-bill-detail", args=[bill.pk]),
            )

            prescriptions = Prescription.objects.filter(
                appointment__patient__user=request.user,
            ).select_related(
                "appointment__patient__user",
            ).filter(
                Q(prescription_id__icontains=query)
                | Q(diagnosis__icontains=query)
                | Q(medicines__medicine_name__icontains=query)
            ).distinct().order_by("-created_at")
            add_results(
                prescriptions,
                "Prescription",
                lambda prescription: prescription.prescription_id,
                lambda prescription: f"{prescription.created_at:%b %d, %Y}",
                lambda prescription: reverse(
                    "prescriptions:my-prescription-detail",
                    args=[prescription.pk],
                ),
            )

    return render(
        request,
        "core/search_results.html",
        {
            "query": query,
            "results": results,
            "return_url": return_url,
        },
    )
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseBadRequest, JsonResponse
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.http import url_has_allowed_host_and_scheme
from django.views.decorators.http import require_POST

from .models import Notification


@login_required
@require_POST
def mark_notifications_read(request):
    notification_ids = request.POST.getlist("notification_ids")
    if notification_ids:
        Notification.objects.filter(
            recipient=request.user,
            pk__in=notification_ids,
            read_at__isnull=True,
        ).update(read_at=timezone.now())

    unread_count = Notification.objects.filter(
        recipient=request.user,
        read_at__isnull=True,
    ).count()
    return JsonResponse({"unread_count": unread_count})


@login_required
@require_POST
def open_notification(request, pk):
    notification = get_object_or_404(
        Notification,
        pk=pk,
        recipient=request.user,
    )

    if not url_has_allowed_host_and_scheme(
        notification.target_url,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return HttpResponseBadRequest("Invalid notification destination.")

    if notification.read_at is None:
        notification.read_at = timezone.now()
        notification.save(update_fields=["read_at"])

    return redirect(notification.target_url)
