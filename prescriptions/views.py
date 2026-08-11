from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render

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

    prescription = get_object_or_404(
        Prescription.objects.select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
        ).prefetch_related(
            "medicines",
        ),
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