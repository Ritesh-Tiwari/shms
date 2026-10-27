from django.contrib import messages
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator
from django.db import transaction
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from accounts.choices import UserRole
from appointments.models import Appointment, AppointmentStatus
from core.decorators import role_required

from .forms import (
    PrescriptionForm,
    PrescriptionMedicineFormSet,
)
from .models import Prescription, PrescriptionStatus


@role_required(UserRole.DOCTOR)
def create_prescription(request, appointment_id):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
        ),
        pk=appointment_id,
    )

    if appointment.doctor.user != request.user:

        messages.error(
            request,
            "You do not have permission to create "
            "a prescription for this appointment.",
        )

        return redirect(
            "appointments:detail",
            pk=appointment.pk,
        )


    # Only completed appointments can have prescriptions.
    if appointment.status != AppointmentStatus.COMPLETED:

        messages.error(
            request,
            "Prescription can only be created "
            "for a completed appointment.",
        )

        return redirect(
            "appointments:detail",
            pk=appointment.pk,
        )

    # Prevent duplicate prescriptions.
    if hasattr(appointment, "prescription"):

        messages.error(
            request,
            "A prescription already exists "
            "for this appointment.",
        )

        return redirect(
            "appointments:detail",
            pk=appointment.pk,
        )

    if request.method == "POST":

        form = PrescriptionForm(
            request.POST,
        )

        formset = PrescriptionMedicineFormSet(
            request.POST,
        )

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    prescription = form.save(commit=False)
                    prescription.appointment = appointment
                    prescription.save()

                    
                    formset.instance = prescription
                    formset.save()

                messages.success(
                    request,
                    "Prescription created successfully.",
                )

                return redirect(
                    "prescriptions:detail",
                    pk=prescription.pk,
                )

            except Exception:
                messages.error(
                    request,
                    "Prescription could not be saved. Please try again.",
                )
    else:

        form = PrescriptionForm()

        formset = PrescriptionMedicineFormSet()

    return render(
        request,
        "prescriptions/create.html",
        {
            "form": form,
            "formset": formset,
            "appointment": appointment,
        },
    )



@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
)
def prescription_detail(request, pk):
    # 1. Base QuerySet
    prescriptions = Prescription.objects.select_related(
        "appointment__patient__user",
        "appointment__doctor__user",
    ).prefetch_related(
        "medicines",
    )

    # 2. Scope filtering: Doctor sirf apne appointment wale prescription dekh sake
    if request.user.role == UserRole.DOCTOR:
        prescriptions = prescriptions.filter(
            appointment__doctor__user=request.user,
        )

    # 3. Fetch with 404 safety
    prescription = get_object_or_404(
        prescriptions,
        pk=pk,
    )

    return render(
        request,
        "prescriptions/detail.html",
        {
            "prescription": prescription,
        },
    )


@role_required(
    UserRole.DOCTOR,
)
def update_prescription(request, pk):

    prescription = get_object_or_404(
        Prescription.objects.select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
        ).prefetch_related(
            "medicines",
        ),
        pk=pk,
    )

    # Only the assigned doctor can update
    # this prescription.
    if prescription.appointment.doctor.user != request.user:

        messages.error(
            request,
            "You do not have permission to update "
            "this prescription.",
        )

        return redirect(
            "prescriptions:detail",
            pk=prescription.pk,
        )

    if request.method == "POST":

        form = PrescriptionForm(
            request.POST,
            instance=prescription,
        )

        formset = PrescriptionMedicineFormSet(
            request.POST,
            instance=prescription,
        )

        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                prescription = form.save()
                formset.instance = prescription
                formset.save()

            messages.success(
                request,
                "Prescription updated successfully.",
            )

            return redirect(
                "prescriptions:detail",
                pk=prescription.pk,
            )

    else:

        form = PrescriptionForm(
            instance=prescription,
        )

        formset = PrescriptionMedicineFormSet(
            instance=prescription,
        )

    return render(
        request,
        "prescriptions/update.html",
        {
            "form": form,
            "formset": formset,
            "prescription": prescription,
        },
    )

@role_required(
    UserRole.PATIENT,
)
def my_prescriptions(request):

    prescriptions = (
        Prescription.objects
        .select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
        )
        .prefetch_related(
            "medicines",
        )
        .filter(
            appointment__patient__user=request.user,
        )
        .order_by(
            "-created_at",
        )
    )
    current_prescription = prescriptions.first()
    active_prescriptions_count = prescriptions.filter(
        status=PrescriptionStatus.ACTIVE,
    ).count()
    completed_prescriptions_count = prescriptions.filter(
        status=PrescriptionStatus.COMPLETED,
    ).count()
    all_prescriptions_count = prescriptions.count()

    paginator = Paginator(
        prescriptions,
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
        "prescriptions/my_prescriptions.html",
        {
            "page_obj": page_obj,
            "current_prescription": current_prescription,
            "active_prescriptions_count": active_prescriptions_count,
            "completed_prescriptions_count": completed_prescriptions_count,
            "all_prescriptions_count": all_prescriptions_count,
        },
    )


@role_required(
    UserRole.PATIENT,
)
def my_prescription_detail(request, pk):

    prescriptions = (
        Prescription.objects
        .select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
        )
        .prefetch_related(
            "medicines",
        )
        .filter(
            appointment__patient__user=request.user,
        )
        .annotate(
        no_of_medicines=Count("medicines")
    )
    )

    

    prescription = get_object_or_404(
        prescriptions,
        pk=pk,
    )

    return render(
        request,
        "prescriptions/my_detail.html",
        {
            "prescription": prescription,
            "no_of_medicines": prescription.no_of_medicines,
        },
    )

@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.PATIENT,
)
def prescription_pdf(request, pk):
    prescription = get_object_or_404(
        Prescription.objects.select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
        ).prefetch_related("medicines"),
        pk=pk,
    )

    appointment = prescription.appointment

    # Patients can download only their own prescriptions.
    if (
        request.user.role == UserRole.PATIENT
        and appointment.patient.user_id != request.user.id
    ):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    # Doctors can download only prescriptions for their appointments.
    if (
        request.user.role == UserRole.DOCTOR
        and appointment.doctor.user_id != request.user.id
    ):
        from django.core.exceptions import PermissionDenied
        raise PermissionDenied

    response = HttpResponse(
        content_type="application/pdf"
    )

    response["Content-Disposition"] = (
        f'attachment; filename="{prescription.prescription_id}.pdf"'
    )

    pdf = canvas.Canvas(
        response,
        pagesize=A4,
    )

    width, height = A4
    y = height - 50

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(50, y, "Smart Health Management System")
    y -= 35

    pdf.setFont("Helvetica-Bold", 14)
    pdf.drawString(50, y, "Prescription")
    y -= 30

    pdf.setFont("Helvetica", 10)

    patient = appointment.patient
    doctor = appointment.doctor

    details = [
        f"Prescription ID: {prescription.prescription_id}",
        f"Patient: {patient.user.get_full_name()}",
        f"Patient ID: {patient.patient_id}",
        f"Doctor: Dr. {doctor.user.get_full_name()}",
        f"Appointment ID: {appointment.appointment_id}",
        f"Date: {prescription.created_at:%d-%m-%Y}",
        f"Status: {prescription.get_status_display()}",
        f"Diagnosis: {prescription.diagnosis}",
        f"Remarks: {prescription.remarks or 'None'}",
    ]

    for line in details:
        if y < 80:
            pdf.showPage()
            pdf.setFont("Helvetica", 10)
            y = height - 50

        pdf.drawString(50, y, line[:110])
        y -= 20

    y -= 10

    pdf.setFont("Helvetica-Bold", 12)
    pdf.drawString(50, y, "Medicines")
    y -= 25

    pdf.setFont("Helvetica", 10)

    for medicine in prescription.medicines.all():
        lines = [
            f"Medicine: {medicine.medicine_name}",
            f"Dosage: {medicine.dosage}",
            f"Frequency: {medicine.frequency}",
            f"Duration: {medicine.duration}",
            f"Instructions: {medicine.instructions or 'None'}",
        ]

        for line in lines:
            if y < 60:
                pdf.showPage()
                pdf.setFont("Helvetica", 10)
                y = height - 50

            pdf.drawString(50, y, line[:110])
            y -= 17

        y -= 8

    pdf.save()

    return response