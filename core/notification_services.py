from django.contrib.auth import get_user_model
from django.urls import reverse

from accounts.choices import UserRole
from .models import Notification

User = get_user_model()
STAFF_ROLES = (UserRole.ADMIN, UserRole.RECEPTIONIST)


def _display_name(user):
    return user.get_full_name() or user.username


def _staff_recipients():
    return User.objects.filter(
        is_active=True,
        role__in=STAFF_ROLES,
    )


def _appointment_url(recipient, appointment):
    if recipient.role == UserRole.PATIENT:
        return reverse(
            "appointments:my-appointment-detail",
            args=[appointment.pk],
        )
    return reverse("appointments:detail", args=[appointment.pk])


def _create_notifications(recipients, actor, message_for_recipient, url_for_recipient):
    actor_name = _display_name(actor)[:150] if actor else ""
    notifications = []
    seen_recipient_ids = set()

    for recipient in recipients:
        if recipient.pk in seen_recipient_ids:
            continue
        seen_recipient_ids.add(recipient.pk)
        notifications.append(Notification(
            recipient=recipient,
            actor_name=actor_name,
            message=message_for_recipient(recipient, actor_name)[:255],
            target_url=url_for_recipient(recipient)[:255],
        ))

    Notification.objects.bulk_create(notifications)


def notify_patient_registered(patient, *, actor):
    patient_user = patient.user
    patient_name = _display_name(patient_user)
    recipients = [patient_user, *_staff_recipients()]

    def message_for(recipient, actor_name):
        if recipient.pk == patient_user.pk:
            return "Your patient profile was created successfully."
        return f"New patient {patient_name} registered."

    def url_for(recipient):
        if recipient.pk == patient_user.pk:
            return reverse("patients:my-profile")
        return reverse("patients:detail", args=[patient.pk])

    _create_notifications(recipients, actor, message_for, url_for)


def notify_appointment_event(appointment, *, actor, event):
    patient_user = appointment.patient.user
    doctor_user = appointment.doctor.user
    patient_name = _display_name(patient_user)
    doctor_name = _display_name(doctor_user)
    recipients = [
        patient_user,
        doctor_user,
        *_staff_recipients(),
    ]

    if event == "booked":
        def message_for(recipient, actor_name):
            if recipient.pk == patient_user.pk:
                return f"Your appointment request with Dr. {doctor_name} was booked."
            if recipient.pk == doctor_user.pk:
                return f"An appointment was booked for {patient_name}."
            return f"Appointment booked for {patient_name} with Dr. {doctor_name}."

    elif event == "rescheduled":
        def message_for(recipient, actor_name):
            if recipient.pk == patient_user.pk:
                return (
                    f"Your appointment with Dr. {doctor_name} was rescheduled "
                    f"by {actor_name or 'staff'}."
                )
            if recipient.pk == doctor_user.pk:
                return (
                    f"Appointment with {patient_name} was rescheduled "
                    f"by {actor_name or 'staff'}."
                )
            return (
                f"Appointment for {patient_name} with Dr. {doctor_name} "
                f"was rescheduled by {actor_name or 'staff'}."
            )

    elif event == "cancelled":
        def message_for(recipient, actor_name):
            if recipient.pk == patient_user.pk:
                if actor and actor.pk == patient_user.pk:
                    return f"You cancelled your appointment with Dr. {doctor_name}."
                return (
                    f"Your appointment with Dr. {doctor_name} was cancelled "
                    f"by {actor_name or 'staff'}."
                )
            if recipient.pk == doctor_user.pk:
                if actor and actor.pk == doctor_user.pk:
                    return f"You cancelled the appointment with {patient_name}."
                return (
                    f"Appointment with {patient_name} was cancelled "
                    f"by {actor_name or 'staff'}."
                )
            return (
                f"Appointment for {patient_name} with Dr. {doctor_name} "
                f"was cancelled by {actor_name or 'staff'}."
            )

    else:
        status_text = appointment.get_status_display().lower()

        def message_for(recipient, actor_name):
            if recipient.pk == patient_user.pk:
                return (
                    f"Your appointment with Dr. {doctor_name} is now "
                    f"{status_text}."
                )
            if recipient.pk == doctor_user.pk:
                return (
                    f"Your appointment with {patient_name} is now "
                    f"{status_text}."
                )
            return (
                f"Appointment for {patient_name} with Dr. {doctor_name} "
                f"is now {status_text}."
            )

    _create_notifications(
        recipients,
        actor,
        message_for,
        lambda recipient: _appointment_url(recipient, appointment),
    )


def notify_payment_created(payment, *, actor):
    billing = payment.billing
    patient_user = billing.patient.user
    doctor_user = billing.appointment.doctor.user
    patient_name = _display_name(patient_user)
    recipients = [patient_user, doctor_user, *_staff_recipients()]

    def message_for(recipient, actor_name):
        if recipient.pk == patient_user.pk:
            return f"Payment of ₹{payment.amount:,.2f} was recorded for your bill."
        if recipient.pk == doctor_user.pk:
            return f"Payment received from {patient_name}."
        return f"Payment of ₹{payment.amount:,.2f} received from {patient_name}."

    def url_for(recipient):
        if recipient.role == UserRole.PATIENT:
            return reverse("billing:my-bill-detail", args=[billing.pk])
        return reverse("billing:detail", args=[billing.pk])

    _create_notifications(recipients, actor, message_for, url_for)


def notify_bill_created(billing, *, actor):
    patient_user = billing.patient.user
    doctor_user = billing.appointment.doctor.user
    patient_name = _display_name(patient_user)
    recipients = [patient_user, doctor_user, *_staff_recipients()]

    def message_for(recipient, actor_name):
        if recipient.pk == patient_user.pk:
            return "A new bill is available for your appointment."
        if recipient.pk == doctor_user.pk:
            return f"A bill was created for {patient_name}."
        return f"A bill was created for {patient_name}."

    def url_for(recipient):
        if recipient.role == UserRole.PATIENT:
            return reverse("billing:my-bill-detail", args=[billing.pk])
        return reverse("billing:detail", args=[billing.pk])

    _create_notifications(recipients, actor, message_for, url_for)


def notify_prescription_saved(prescription, *, actor, updated=False):
    appointment = prescription.appointment
    patient_user = appointment.patient.user
    doctor_user = appointment.doctor.user
    patient_name = _display_name(patient_user)
    recipients = [patient_user, doctor_user, *_staff_recipients()]

    def message_for(recipient, actor_name):
        if recipient.pk == patient_user.pk:
            action = "updated" if updated else "added"
            return f"Dr. {_display_name(doctor_user)} {action} a prescription for you."
        if recipient.pk == doctor_user.pk:
            action = "updated" if updated else "created"
            return f"You {action} a prescription for {patient_name}."
        action = "updated" if updated else "created"
        return f"Prescription {action} for {patient_name}."

    def url_for(recipient):
        if recipient.role == UserRole.PATIENT:
            return reverse(
                "prescriptions:my-prescription-detail",
                args=[prescription.pk],
            )
        if recipient.role == UserRole.DOCTOR:
            return reverse("prescriptions:detail", args=[prescription.pk])
        return reverse("appointments:detail", args=[appointment.pk])

    _create_notifications(recipients, actor, message_for, url_for)
