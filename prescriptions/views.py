from django.contrib import messages
from django.db.models.aggregates import Count
from django.db.models.aggregates import Count
from django.shortcuts import get_object_or_404, redirect, render
from django.core.paginator import Paginator

from accounts.choices import UserRole
from appointments.models import Appointment, AppointmentStatus
from core.decorators import role_required

from .forms import (
    PrescriptionForm,
    PrescriptionMedicineFormSet,
)
from .models import Prescription


@role_required(
    UserRole.DOCTOR,
    UserRole.ADMIN
)
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

            prescription = form.save(
                commit=False,
            )

            prescription.appointment = appointment

            prescription.save()

            medicines = formset.save(
                commit=False,
            )

            for medicine in medicines:

                medicine.prescription = prescription
                medicine.save()

            messages.success(
                request,
                "Prescription created successfully.",
            )

            return redirect(
                "prescriptions:detail",
                pk=prescription.pk,
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

            form.save()

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
    current_prescription = prescriptions.first()  # Get the most recent prescription

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