import csv
from decimal import Decimal

from django.core.paginator import Paginator
from django.db.models import Sum
from django.http import HttpResponse
from django.shortcuts import render
from django.utils import timezone

from accounts.choices import UserRole
from appointments.models import Appointment
from billing.models import Billing
from core.decorators import role_required
from doctors.models import DoctorSchedule
from patients.models import Patient
from prescriptions.models import Prescription

from .forms import ReportFilterForm


def _date_range(queryset, field, start_date, end_date, is_datetime=False):
    lookup_field = f"{field}__date" if is_datetime else field
    if start_date:
        queryset = queryset.filter(**{f"{lookup_field}__gte": start_date})
    if end_date:
        queryset = queryset.filter(**{f"{lookup_field}__lte": end_date})
    return queryset


def _patient_row(patient):
    user = patient.user
    return (
        patient.patient_id,
        user.get_full_name() or user.username,
        user.email,
        user.phone_number,
        patient.date_of_birth.isoformat(),
        patient.get_gender_display(),
        patient.city,
        timezone.localtime(patient.created_at).date().isoformat(),
    )


def _appointment_row(appointment):
    patient_user = appointment.patient.user
    doctor_user = appointment.doctor.user
    return (
        appointment.appointment_id,
        patient_user.get_full_name() or patient_user.username,
        doctor_user.get_full_name() or doctor_user.username,
        appointment.appointment_date.isoformat(),
        appointment.appointment_time.strftime("%H:%M"),
        appointment.get_status_display(),
        appointment.reason_for_visit,
    )


def _doctor_schedule_row(schedule):
    doctor_user = schedule.doctor.user
    return (
        schedule.doctor.doctor_id,
        doctor_user.get_full_name() or doctor_user.username,
        schedule.doctor.get_specialization_display(),
        schedule.doctor.get_availability_display(),
        schedule.get_weekday_display(),
        schedule.start_time.strftime("%H:%M"),
        schedule.end_time.strftime("%H:%M"),
        "Active" if schedule.is_active else "Inactive",
    )


def _prescription_row(prescription):
    appointment = prescription.appointment
    patient_user = appointment.patient.user
    doctor_user = appointment.doctor.user
    return (
        prescription.prescription_id,
        appointment.appointment_id,
        patient_user.get_full_name() or patient_user.username,
        doctor_user.get_full_name() or doctor_user.username,
        prescription.diagnosis,
        prescription.get_status_display(),
        "; ".join(
            (
                f"{medicine.medicine_name} ({medicine.dosage}; "
                f"{medicine.frequency}; {medicine.duration})"
            )
            for medicine in prescription.medicines.all()
        ),
        timezone.localtime(prescription.created_at).date().isoformat(),
    )


def _billing_row(billing):
    appointment = billing.appointment
    patient_user = billing.patient.user
    doctor_user = appointment.doctor.user
    return (
        billing.bill_id,
        appointment.appointment_id,
        patient_user.get_full_name() or patient_user.username,
        doctor_user.get_full_name() or doctor_user.username,
        timezone.localtime(billing.bill_date).date().isoformat(),
        billing.amount,
        billing.tax_amount,
        billing.total_amount,
        billing.get_payment_status_display(),
    )


def _payment_status_rows(billing):
    paid_amount = billing.paid_amount or Decimal("0.00")
    outstanding = billing.total_amount - paid_amount
    payments = list(billing.payments.all())
    patient_user = billing.patient.user

    if not payments:
        return [
            (
                "",
                "",
                billing.bill_id,
                patient_user.get_full_name() or patient_user.username,
                "",
                "",
                "",
                billing.get_payment_status_display(),
                outstanding,
            )
        ]

    return [
        (
            payment.payment_id,
            payment.transaction_reference,
            billing.bill_id,
            patient_user.get_full_name() or patient_user.username,
            payment.get_payment_method_display(),
            payment.amount,
            timezone.localtime(payment.payment_date).date().isoformat(),
            billing.get_payment_status_display(),
            outstanding,
        )
        for payment in payments
    ]


def _get_report(report_key, start_date, end_date):
    if report_key == "patients":
        queryset = Patient.objects.select_related("user").order_by("-created_at")
        queryset = _date_range(
            queryset, "created_at", start_date, end_date, is_datetime=True
        )
        return (
            "Patient Registration Report",
            (
                "Patient ID",
                "Patient Name",
                "Email",
                "Phone",
                "Date of Birth",
                "Gender",
                "City",
                "Registered On",
            ),
            queryset,
            _patient_row,
        )

    if report_key == "appointments":
        queryset = Appointment.objects.select_related(
            "patient__user", "doctor__user"
        ).order_by("-appointment_date", "-appointment_time")
        queryset = _date_range(
            queryset, "appointment_date", start_date, end_date
        )
        return (
            "Appointment Summary Report",
            (
                "Appointment ID",
                "Patient",
                "Doctor",
                "Date",
                "Time",
                "Status",
                "Reason",
            ),
            queryset,
            _appointment_row,
        )

    if report_key == "doctor_schedules":
        queryset = DoctorSchedule.objects.select_related(
            "doctor__user"
        ).order_by("doctor__doctor_id", "weekday", "start_time")
        return (
            "Doctor Schedule Report",
            (
                "Doctor ID",
                "Doctor",
                "Specialization",
                "Availability",
                "Weekday",
                "Start Time",
                "End Time",
                "Schedule Status",
            ),
            queryset,
            _doctor_schedule_row,
        )

    if report_key == "prescriptions":
        queryset = Prescription.objects.select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
        ).prefetch_related("medicines").order_by("-created_at")
        queryset = _date_range(
            queryset, "created_at", start_date, end_date, is_datetime=True
        )
        return (
            "Prescription Report",
            (
                "Prescription ID",
                "Appointment ID",
                "Patient",
                "Doctor",
                "Diagnosis",
                "Medicines",
                "Status",
                "Created On",
            ),
            queryset,
            _prescription_row,
        )

    if report_key == "billing_revenue":
        queryset = Billing.objects.select_related(
            "appointment__doctor__user", "patient__user"
        ).order_by("-bill_date")
        queryset = _date_range(
            queryset, "bill_date", start_date, end_date, is_datetime=True
        )
        return (
            "Billing & Revenue Report",
            (
                "Bill ID",
                "Appointment ID",
                "Patient",
                "Doctor",
                "Bill Date",
                "Amount",
                "Tax",
                "Total",
                "Payment Status",
            ),
            queryset,
            _billing_row,
        )

    if report_key == "payment_status":
        queryset = Billing.objects.select_related(
            "patient__user"
        ).prefetch_related("payments").annotate(
            paid_amount=Sum("payments__amount")
        ).order_by("-bill_date")
        queryset = _date_range(
            queryset, "bill_date", start_date, end_date, is_datetime=True
        )
        return (
            "Payment Status Report",
            (
                "Payment ID",
                "Transaction Reference",
                "Bill ID",
                "Patient",
                "Payment Method",
                "Payment Amount",
                "Payment Date",
                "Bill Status",
                "Outstanding",
            ),
            queryset,
            _payment_status_rows,
        )

    raise ValueError(f"Unknown report: {report_key}")


def _csv_safe(value):
    value = str(value) if value is not None else ""
    if value.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")):
        return f"'{value}"
    return value


def _report_form(request):
    data = request.GET if request.GET else {"report": "patients"}
    return ReportFilterForm(data)


@role_required(UserRole.ADMIN)
def report_list(request):
    form = _report_form(request)
    context = {"form": form, "page_obj": None}

    if form.is_valid():
        report_key = form.cleaned_data["report"]
        title, columns, queryset, row_builder = _get_report(
            report_key,
            form.cleaned_data["start_date"],
            form.cleaned_data["end_date"],
        )
        page_obj = Paginator(queryset, 50).get_page(request.GET.get("page"))
        context.update(
            {
                "report_title": title,
                "columns": columns,
                "rows": [row_builder(item) for item in page_obj.object_list],
                "page_obj": page_obj,
                "selected_report": report_key,
            }
        )

    return render(request, "dashboard/reports.html", context)


@role_required(UserRole.ADMIN)
def report_download(request):
    form = _report_form(request)
    if not form.is_valid():
        return render(
            request,
            "dashboard/reports.html",
            {"form": form, "page_obj": None},
            status=400,
        )

    report_key = form.cleaned_data["report"]
    _, columns, queryset, row_builder = _get_report(
        report_key,
        form.cleaned_data["start_date"],
        form.cleaned_data["end_date"],
    )
    start_date = form.cleaned_data["start_date"]
    end_date = form.cleaned_data["end_date"]

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = (
        f'attachment; filename="shms_{report_key}_'
        f'{start_date or "all"}_{end_date or "all"}.csv"'
    )
    writer = csv.writer(response)
    writer.writerow([_csv_safe(column) for column in columns])

    for item in queryset.iterator(chunk_size=500):
        report_rows = row_builder(item)
        if report_key == "payment_status":
            for row in report_rows:
                writer.writerow([_csv_safe(value) for value in row])
        else:
            writer.writerow([_csv_safe(value) for value in report_rows])

    return response
