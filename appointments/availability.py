from datetime import date, datetime, time, timedelta
from django.utils import timezone

from doctors.models import Doctor, DoctorLeave, DoctorSchedule
from .models import Appointment, AppointmentStatus


SLOT_DURATION_MINUTES = 30
BOOKING_WINDOW_DAYS = 60


ACTIVE_APPOINTMENT_STATUSES = [
    AppointmentStatus.SCHEDULED,
    AppointmentStatus.CONFIRMED,
]


def get_booking_limit():
    return timezone.localdate() + timedelta(
        days=BOOKING_WINDOW_DAYS
    )


def is_doctor_bookable(doctor):
    """
    Check whether the doctor can accept appointments.
    """

    if not doctor:
        return False

    return (
        doctor.user.is_active
        and doctor.availability == "AVAILABLE"
    )


def is_valid_booking_date(appointment_date):
    """
    Allow bookings from today through the booking horizon.
    """

    if not appointment_date:
        return False

    today = timezone.localdate()
    booking_limit = get_booking_limit()

    return today <= appointment_date <= booking_limit


def get_scheduled_slots(doctor, appointment_date):
    """
    Generate 30-minute slots from the doctor's recurring schedule.

    Example:
        Schedule: 09:00 - 11:00

        Slots:
        09:00
        09:30
        10:00
        10:30
    """

    if not doctor or not appointment_date:
        return []

    if not is_doctor_bookable(doctor):
        return []

    if not is_valid_booking_date(appointment_date):
        return []

    # Full-day doctor leave means no available slots.
    if DoctorLeave.objects.filter(
        doctor=doctor,
        leave_date=appointment_date,
        is_active=True,
    ).exists():
        return []

    weekday = appointment_date.weekday()

    schedules = DoctorSchedule.objects.filter(
        doctor=doctor,
        weekday=weekday,
        is_active=True,
    ).order_by("start_time")

    available_slots = set()

    now = timezone.localtime()

    for schedule in schedules:

        slot_start = datetime.combine(
            appointment_date,
            schedule.start_time,
        )

        schedule_end = datetime.combine(
            appointment_date,
            schedule.end_time,
        )

        while True:

            slot_end = slot_start + timedelta(
                minutes=SLOT_DURATION_MINUTES
            )

            # Do not create a slot extending beyond the schedule.
            if slot_end > schedule_end:
                break

            slot_time = slot_start.time()

            # Exclude slots that have already passed today.
            if appointment_date == now.date():

                current_datetime = now.replace(
                    tzinfo=None,
                    second=0,
                    microsecond=0,
                )

                if slot_start <= current_datetime:
                    slot_start = slot_end
                    continue

            available_slots.add(slot_time)

            slot_start = slot_end

    return sorted(available_slots)


def get_available_slots(
    doctor,
    appointment_date,
    exclude_appointment_id=None,
):
    """
    Return available slots after excluding existing active bookings.
    """

    scheduled_slots = get_scheduled_slots(
        doctor,
        appointment_date,
    )

    if not scheduled_slots:
        return []

    booked_appointments = Appointment.objects.filter(
        doctor=doctor,
        appointment_date=appointment_date,
        status__in=ACTIVE_APPOINTMENT_STATUSES,
    )

    # While rescheduling, do not treat the current appointment
    # as a conflicting booking against itself.
    if exclude_appointment_id:
        booked_appointments = booked_appointments.exclude(
            pk=exclude_appointment_id
        )

    booked_times = set(
        booked_appointments.values_list(
            "appointment_time",
            flat=True,
        )
    )

    return [
        slot
        for slot in scheduled_slots
        if slot not in booked_times
    ]


def get_available_dates(doctor):
    """
    Return dates within the booking window that have at least
    one available slot.
    """

    if not is_doctor_bookable(doctor):
        return []

    today = timezone.localdate()
    booking_limit = get_booking_limit()

    available_dates = []

    current_date = today

    while current_date <= booking_limit:

        slots = get_available_slots(
            doctor,
            current_date,
        )

        if slots:
            available_dates.append(current_date)

        current_date += timedelta(days=1)

    return available_dates


def get_booking_error(
    doctor,
    appointment_date,
    appointment_time,
    exclude_appointment_id=None,
):
    """
    Central server-side booking validation.

    Returns:
        None when valid.
        (field_name, error_message) when invalid.
    """

    if not doctor:
        return (
            "doctor",
            "Please select a doctor.",
        )

    if not appointment_date:
        return (
            "appointment_date",
            "Please select an appointment date.",
        )

    if not appointment_time:
        return (
            "appointment_time",
            "Please select an appointment time.",
        )

    if not is_doctor_bookable(doctor):
        return (
            "doctor",
            "This doctor is currently unavailable.",
        )

    if not is_valid_booking_date(appointment_date):
        return (
            "appointment_date",
            "Choose a date between today and the next 60 days.",
        )

    now = timezone.localtime()

    if appointment_date == now.date():

        current_time = now.time().replace(
            second=0,
            microsecond=0,
        )

        if appointment_time <= current_time:
            return (
                "appointment_time",
                "Appointment time must be in the future.",
            )

    if DoctorLeave.objects.filter(
        doctor=doctor,
        leave_date=appointment_date,
        is_active=True,
    ).exists():
        return (
            "appointment_date",
            "This doctor is on leave on the selected date.",
        )

    available_slots = get_available_slots(
        doctor=doctor,
        appointment_date=appointment_date,
        exclude_appointment_id=exclude_appointment_id,
    )

    if appointment_time not in available_slots:
        return (
            "appointment_time",
            "This time slot is unavailable. Please select another slot.",
        )

    return None