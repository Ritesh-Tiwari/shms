from django.contrib import messages
from django.shortcuts import get_object_or_404, redirect, render
from django.http import HttpResponse
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from appointments.models import Appointment, AppointmentStatus
from core.decorators import role_required
from core.notification_services import (
    notify_bill_created,
    notify_payment_created,
)
from accounts.choices import UserRole
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied

from accounts.models import User

from .forms import BillingForm, PaymentForm
from .models import (
    Billing,
    Payment,
    PaymentStatus,
)


@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
)
def create_bill(request, appointment_id):

    appointment = get_object_or_404(
        Appointment.objects.select_related(
            "patient__user",
            "doctor__user",
        ),
        pk=appointment_id,
    )

    # Only completed appointments can have a final bill.
    if appointment.status != AppointmentStatus.COMPLETED:

        messages.error(
            request,
            "Bill can only be created "
            "for a completed appointment.",
        )

        return redirect(
            "appointments:detail",
            pk=appointment.pk,
        )

    # Only the assigned doctor can create the bill.
    if (
        request.user.role != UserRole.ADMIN
        and request.user != appointment.doctor.user
    ):
        messages.error(
            request,
            "You do not have permission "
            "to create this bill.",
        )

        return redirect(
            "appointments:detail",
            pk=appointment.pk,
        )

    # Prevent duplicate billing.
    if hasattr(appointment, "billing"):

        messages.error(
            request,
            "A bill already exists "
            "for this appointment.",
        )

        return redirect(
            "billing:detail",
            pk=appointment.billing.pk,
        )

    if request.method == "POST":

        form = BillingForm(request.POST)

        if form.is_valid():

            billing = form.save(
                commit=False,
            )

            billing.appointment = appointment
            billing.patient = appointment.patient

            # Consultation fee comes from the doctor.
            billing.amount = (
                appointment.doctor.consultation_fee
            )

            billing.save()
            notify_bill_created(billing, actor=request.user)

            messages.success(
                request,
                "Bill created successfully.",
            )

            return redirect(
                "billing:detail",
                pk=billing.pk,
            )

    else:

        form = BillingForm()

    return render(
        request,
        "billing/create.html",
        {
            "form": form,
            "appointment": appointment,
        },
    )


@role_required(
    UserRole.ADMIN,
    UserRole.RECEPTIONIST,
    UserRole.DOCTOR,
)
def billing_detail(request, pk):

    billings = Billing.objects.select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
            "patient__user",
        ).prefetch_related(
            "payments",
        )
    
    if request.user.role == UserRole.DOCTOR:
        billings = billings.filter(
            appointment__doctor__user=request.user,
        )

    billing = get_object_or_404(
        billings,
        pk=pk,
    )

    paid_amount = sum(
        payment.amount
        for payment in billing.payments.all()
    )

    remaining_amount = (
        billing.total_amount - paid_amount
    )

    return render(
        request,
        "billing/detail.html",
        {
            "billing": billing,
            "paid_amount": paid_amount,
            "remaining_amount": remaining_amount,
        },
    )

@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
)
def create_payment(request, billing_id):

    billing = get_object_or_404(
        Billing.objects.select_related(
            "appointment__patient__user",
            "appointment__doctor__user",
            "patient__user",
        ).prefetch_related(
            "payments",
        ),
        pk=billing_id,
    )

    # Only the assigned doctor or admin can record payment.
    if (
        request.user.role != UserRole.ADMIN
        and request.user != billing.appointment.doctor.user
    ):

        messages.error(
            request,
            "You do not have permission "
            "to record this payment.",
        )

        return redirect(
            "billing:detail",
            pk=billing.pk,
        )

    # Calculate already paid amount.
    paid_amount = sum(
        payment.amount
        for payment in billing.payments.all()
    )

    remaining_amount = (
        billing.total_amount - paid_amount
    )

    # Prevent payment when the bill is already fully paid.
    if remaining_amount <= 0:

        messages.info(
            request,
            "This bill has already been fully paid.",
        )

        return redirect(
            "billing:detail",
            pk=billing.pk,
        )

    if request.method == "POST":

        form = PaymentForm(request.POST)

        if form.is_valid():

            payment_amount = form.cleaned_data[
                "amount"
            ]

            # Prevent overpayment.
            if payment_amount > remaining_amount:

                form.add_error(
                    "amount",
                    (
                        "Payment cannot exceed "
                        f"the remaining amount "
                        f"of ₹{remaining_amount}."
                    ),
                )

            else:

                payment = form.save(
                    commit=False,
                )

                payment.billing = billing
                payment.save()
                notify_payment_created(payment, actor=request.user)

                # Recalculate payment status.
                new_paid_amount = (
                    paid_amount + payment_amount
                )

                if new_paid_amount >= billing.total_amount:

                    billing.payment_status = (
                        PaymentStatus.PAID
                    )

                elif new_paid_amount > 0:

                    billing.payment_status = (
                        PaymentStatus.PARTIAL
                    )

                else:

                    billing.payment_status = (
                        PaymentStatus.PENDING
                    )

                billing.save(
                    update_fields=[
                        "payment_status",
                    ]
                )

                messages.success(
                    request,
                    "Payment recorded successfully.",
                )

                return redirect(
                    "billing:detail",
                    pk=billing.pk,
                )

    else:

        form = PaymentForm(
            initial={
                "amount": remaining_amount,
            }
        )

    return render(
        request,
        "billing/payment.html",
        {
            "form": form,
            "billing": billing,
            "paid_amount": paid_amount,
            "remaining_amount": remaining_amount,
        },
    )

@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
)
def payment_receipt(request, payment_id):

    payments = Payment.objects.select_related(
        "billing__patient__user",
        "billing__appointment__doctor__user",
        "billing__appointment",
    )

    if request.user.role == UserRole.DOCTOR:
        payments = payments.filter(
            billing__appointment__doctor__user=request.user
        )

    payment = get_object_or_404(
        payments,
        pk=payment_id,
    )

    billing = payment.billing

    # Calculate cumulative amount paid up to this payment.
    previous_paid_amount = sum(
        item.amount
        for item in billing.payments.all()
        if item.payment_date < payment.payment_date
        or (
            item.payment_date == payment.payment_date
            and item.pk <= payment.pk
        )
    )

    remaining_amount = (
        billing.total_amount - previous_paid_amount
    )

    return render(
        request,
        "billing/receipt.html",
        {
            "payment": payment,
            "billing": billing,
            "total_paid": previous_paid_amount,
            "remaining_amount": remaining_amount,
        },
    )


@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.PATIENT,
    UserRole.RECEPTIONIST,
)
def billing_pdf(request, pk):
    billings = Billing.objects.select_related(
        "appointment__doctor__user",
        "patient__user",
    ).prefetch_related("payments")

    if request.user.role == UserRole.PATIENT:
        billings = billings.filter(patient__user=request.user)
    elif request.user.role == UserRole.DOCTOR:
        billings = billings.filter(appointment__doctor__user=request.user)

    billing = get_object_or_404(billings, pk=pk)
    payments = list(billing.payments.all())
    paid_amount = sum((payment.amount for payment in payments), start=0)
    remaining_amount = billing.total_amount - paid_amount

    response = HttpResponse(content_type="application/pdf")
    response["Content-Disposition"] = (
        f'attachment; filename="invoice_{billing.bill_id}.pdf"'
    )

    pdf = canvas.Canvas(response, pagesize=A4)
    width, height = A4
    y = height - 50

    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawCentredString(width / 2, y, "SHMS")
    y -= 25
    pdf.setFont("Helvetica", 10)
    pdf.drawCentredString(width / 2, y, "Smart Health Management System")
    y -= 45

    pdf.setFont("Helvetica-Bold", 15)
    pdf.drawString(50, y, "Invoice")
    y -= 30

    invoice_data = [
        ("Bill ID", billing.bill_id),
        ("Appointment", billing.appointment.appointment_id),
        ("Patient ID", billing.patient.patient_id),
        ("Patient Name", billing.patient.user.get_full_name()),
        ("Doctor ID", billing.appointment.doctor.doctor_id),
        ("Doctor Name", billing.appointment.doctor.user.get_full_name()),
        ("Bill Date", billing.bill_date.strftime("%d %b %Y, %I:%M %p")),
        ("Payment Status", billing.get_payment_status_display()),
        ("Amount", f"Rs. {billing.amount}"),
        ("Tax", f"{billing.get_tax_type_display()} - Rs. {billing.tax_amount}"),
        ("Total", f"Rs. {billing.total_amount}"),
        ("Total Paid", f"Rs. {paid_amount}"),
        ("Remaining Due", f"Rs. {remaining_amount}"),
    ]

    for label, value in invoice_data:
        if y < 70:
            pdf.showPage()
            y = height - 50
        pdf.setFont("Helvetica-Bold", 10)
        pdf.drawString(60, y, f"{label}:")
        pdf.setFont("Helvetica", 10)
        pdf.drawString(220, y, str(value)[:100])
        y -= 22

    if payments:
        y -= 12
        if y < 70:
            pdf.showPage()
            y = height - 50
        pdf.setFont("Helvetica-Bold", 12)
        pdf.drawString(60, y, "Payments")
        y -= 24
        pdf.setFont("Helvetica-Bold", 9)
        pdf.drawString(60, y, "Payment ID")
        pdf.drawString(160, y, "Date")
        pdf.drawString(285, y, "Method")
        pdf.drawString(390, y, "Amount")
        y -= 18

        for payment in payments:
            if y < 55:
                pdf.showPage()
                y = height - 50
                pdf.setFont("Helvetica-Bold", 9)
                pdf.drawString(60, y, "Payment ID")
                pdf.drawString(160, y, "Date")
                pdf.drawString(285, y, "Method")
                pdf.drawString(390, y, "Amount")
                y -= 18
            pdf.setFont("Helvetica", 9)
            pdf.drawString(60, y, payment.payment_id)
            pdf.drawString(160, y, payment.payment_date.strftime("%d %b %Y"))
            pdf.drawString(285, y, payment.get_payment_method_display())
            pdf.drawString(390, y, f"Rs. {payment.amount}")
            y -= 18

    pdf.save()
    return response


@role_required(
    UserRole.ADMIN,
    UserRole.DOCTOR,
    UserRole.PATIENT,
    UserRole.RECEPTIONIST,
)
def payment_receipt_pdf(request, payment_id):

    user = request.user

    payments = Payment.objects.select_related(
        "billing__patient__user",
        "billing__appointment__doctor__user",
        "billing__appointment",
    )

    # Patient → only own payments
    if user.role == UserRole.PATIENT:
        payments = payments.filter(
            billing__patient__user=user
        )

    # Doctor → only payments related to their appointments
    elif user.role == UserRole.DOCTOR:
        payments = payments.filter(
            billing__appointment__doctor__user=user
        )

    # Admin + Receptionist → all payments
    # No additional filter required.

    payment = get_object_or_404(
        payments,
        pk=payment_id,
    )

    billing = payment.billing

    # PDF generation...

    # Calculate cumulative paid amount up to this payment.
    previous_paid_amount = sum(
        item.amount
        for item in billing.payments.all()
        if item.payment_date < payment.payment_date
        or (
            item.payment_date == payment.payment_date
            and item.pk <= payment.pk
        )
    )

    remaining_amount = (
        billing.total_amount - previous_paid_amount
    )

    response = HttpResponse(
        content_type="application/pdf"
    )

    response[
        "Content-Disposition"
    ] = (
        f'attachment; '
        f'filename="receipt_{payment.payment_id}.pdf"'
    )

    pdf = canvas.Canvas(
        response,
        pagesize=A4,
    )

    width, height = A4

    y = height - 50

    pdf.setFont(
        "Helvetica-Bold",
        18,
    )

    pdf.drawCentredString(
        width / 2,
        y,
        "SHMS",
    )

    y -= 25

    pdf.setFont(
        "Helvetica",
        10,
    )

    pdf.drawCentredString(
        width / 2,
        y,
        "Smart Health Management System",
    )

    y -= 35

    pdf.setFont(
        "Helvetica-Bold",
        15,
    )

    pdf.drawString(
        50,
        y,
        "Payment Receipt",
    )

    y -= 30

    pdf.setFont(
        "Helvetica",
        10,
    )

    receipt_data = [
        (
            "Payment ID",
            payment.payment_id,
        ),
        (
            "Bill ID",
            billing.bill_id,
        ),
        (
            "Appointment",
            billing.appointment.appointment_id,
        ),
        (
            "Patient ID",
            billing.patient.patient_id,
        ),
        (
            "Patient Name",
            billing.patient.user.get_full_name(),
        ),
        (
            "Doctor ID",
            billing.appointment.doctor.doctor_id,
        ),
        (
            "Doctor Name",
            billing.appointment.doctor.user.get_full_name(),
        ),
        (
            "Payment Amount",
            f"Rs. {payment.amount}",
        ),
        (
            "Payment Type",
            payment.get_payment_type_display(),
        ),
        (
            "Payment Method",
            payment.get_payment_method_display(),
        ),
        (
            "Transaction Reference",
            payment.transaction_reference or "-",
        ),
        (
            "Payment Date",
            payment.payment_date.strftime(
                "%d %b %Y, %I:%M %p"
            ),
        ),
        (
            "Total Bill",
            f"Rs. {billing.total_amount}",
        ),
        (
            "Total Paid",
            f"Rs. {previous_paid_amount}",
        ),
        (
            "Remaining Due",
            f"Rs. {remaining_amount}",
        ),
    ]

    for label, value in receipt_data:

        pdf.setFont(
            "Helvetica-Bold",
            10,
        )

        pdf.drawString(
            60,
            y,
            f"{label}:",
        )

        pdf.setFont(
            "Helvetica",
            10,
        )

        pdf.drawString(
            220,
            y,
            str(value),
        )

        y -= 22

    y -= 15

    pdf.line(
        50,
        y,
        width - 50,
        y,
    )

    y -= 30

    pdf.setFont(
        "Helvetica-Bold",
        11,
    )

    pdf.drawCentredString(
        width / 2,
        y,
        "Payment received successfully.",
    )

    pdf.showPage()
    pdf.save()

    return response




@role_required(
    UserRole.PATIENT,
)
def my_bills(request):

    billings = (
        Billing.objects
        .select_related(
            "patient__user",
            "appointment__doctor__user",
        )
        .prefetch_related(
            "payments",
        )
        .filter(
            patient__user=request.user,
        )
        .order_by(
            "-bill_date",
        )
    )

    return render(
        request,
        "billing/my_bills.html",
        {
            "billings": billings,
        },
    )


@role_required(
    UserRole.PATIENT,
)
def my_bill_detail(request, pk):

    billings = (
        Billing.objects
        .select_related(
            "patient__user",
            "appointment__doctor__user",
        )
        .prefetch_related(
            "payments",
        )
        .filter(
            patient__user=request.user,
        )
    )

    billing = get_object_or_404(
        billings,
        pk=pk,
    )

    paid_amount = sum(
        payment.amount
        for payment in billing.payments.all()
    )

    remaining_amount = (
        billing.total_amount - paid_amount
    )

    return render(
        request,
        "billing/my_detail.html",
        {
            "billing": billing,
            "paid_amount": paid_amount,
            "remaining_amount": remaining_amount,
        },
    )


@role_required(
    UserRole.PATIENT,
)
def my_payment_receipts(request):

    payments = (
        Payment.objects
        .select_related(
            "billing__patient__user",
            "billing__appointment__doctor__user",
            "billing__appointment",
        )
        .filter(
            billing__patient__user=request.user,
        )
        .order_by(
            "-payment_date",
        )
    )

    return render(
        request,
        "billing/my_receipts.html",
        {
            "payments": payments,
        },
    )


@role_required(
    UserRole.PATIENT,
)
def my_payment_receipt(request, payment_id):

    payments = (
        Payment.objects
        .select_related(
            "billing__patient__user",
            "billing__appointment__doctor__user",
            "billing__appointment",
        )
        .filter(
            billing__patient__user=request.user,
        )
    )

    payment = get_object_or_404(
        payments,
        pk=payment_id,
    )

    billing = payment.billing

    previous_paid_amount = sum(
        item.amount
        for item in billing.payments.all()
        if item.payment_date < payment.payment_date
        or (
            item.payment_date == payment.payment_date
            and item.pk <= payment.pk
        )
    )

    remaining_amount = (
        billing.total_amount - previous_paid_amount
    )

    return render(
        request,
        "billing/my_receipt.html",
        {
            "payment": payment,
            "billing": billing,
            "total_paid": previous_paid_amount,
            "remaining_amount": remaining_amount,
        },
    )