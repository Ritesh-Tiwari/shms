from django.utils import timezone
from django import forms

from .models import Appointment
from doctors.models import DoctorSchedule

def validate_doctor_schedule(
    form,
    doctor,
    appointment_date,
    appointment_time,
):
    if not doctor or not appointment_date or not appointment_time:
        return

    if doctor.availability != "AVAILABLE":
        form.add_error(
            "doctor",
            "This doctor is currently unavailable.",
        )
        return

    schedule_exists = DoctorSchedule.objects.filter(
        doctor=doctor,
        weekday=appointment_date.weekday(),
        is_active=True,
        start_time__lte=appointment_time,
        end_time__gt=appointment_time,
    ).exists()

    if not schedule_exists:
        form.add_error(
            "appointment_time",
            "The doctor is not scheduled at this time.",
        )


class AppointmentForm(forms.ModelForm):

    class Meta:

        model = Appointment

        fields = [
            "patient",
            "doctor",
            "appointment_date",
            "appointment_time",
            "reason_for_visit",
        ]

        widgets = {
            "appointment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    
                }
            ),
            "appointment_time": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),
            "reason_for_visit": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        appointment_date = cleaned_data.get(
            "appointment_date"
        )

        appointment_time = cleaned_data.get(
            "appointment_time"
        )

        validate_doctor_schedule(
            self,
            self.instance.doctor,
            cleaned_data.get("appointment_date"),
            cleaned_data.get("appointment_time"),
        )

        if not appointment_date or not appointment_time:
            return cleaned_data

        now = timezone.localtime()
        current_date = now.date()
        current_time = now.time()

        if appointment_date < current_date:

            self.add_error(
                "appointment_date",
                "Appointment date cannot be in the past.",
            )

        elif (
            appointment_date == current_date
            and appointment_time <= current_time
        ):

            self.add_error(
                "appointment_time",
                "Appointment time must be in the future.",
            )

        return cleaned_data

class AppointmentUpdateForm(forms.ModelForm):

    class Meta:

        model = Appointment

        fields = [
            "appointment_date",
            "appointment_time",
            "reason_for_visit",
        ]

        widgets = {
            "appointment_date": forms.DateInput(
                attrs={
                    "type": "date",
                    
                    
                }
            ),
            "appointment_time": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),
            "reason_for_visit": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        appointment_date = cleaned_data.get(
            "appointment_date"
        )

        appointment_time = cleaned_data.get(
            "appointment_time"
        )
        validate_doctor_schedule(
            self,
            self.instance.doctor,
            cleaned_data.get("appointment_date"),
            cleaned_data.get("appointment_time"),
        )

        if not appointment_date or not appointment_time:
            return cleaned_data

        now = timezone.localtime()
        current_date = now.date()
        current_time = now.time()

        if appointment_date < current_date:

            self.add_error(
                "appointment_date",
                "Appointment date cannot be in the past.",
            )

        elif (
            appointment_date == current_date
            and appointment_time <= current_time
        ):

            self.add_error(
                "appointment_time",
                "Appointment time must be in the future.",
            )

        return cleaned_data


class PatientAppointmentForm(forms.ModelForm):

    class Meta:

        model = Appointment

        fields = [
            "doctor",
            "appointment_date",
            "appointment_time",
            "reason_for_visit",
        ]

        widgets = {
            "appointment_date": forms.DateInput(
                attrs={
                    "type": "date",
                }
            ),
            "appointment_time": forms.TimeInput(
                attrs={
                    "type": "time",
                }
            ),
            "reason_for_visit": forms.Textarea(
                attrs={
                    "rows": 3,
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()
        
        appointment_date = cleaned_data.get(
            "appointment_date"
        )

        appointment_time = cleaned_data.get(
            "appointment_time"
        )

        validate_doctor_schedule(
            self,
            cleaned_data.get("doctor"),
            cleaned_data.get("appointment_date"),
            cleaned_data.get("appointment_time"),
        )
    
        if not appointment_date or not appointment_time:
            return cleaned_data

        now = timezone.localtime()
        current_date = now.date()
        current_time = now.time()

        if appointment_date < current_date:

            self.add_error(
                "appointment_date",
                "Appointment date cannot be in the past.",
            )

        elif (
            appointment_date == current_date
            and appointment_time <= current_time
        ):

            self.add_error(
                "appointment_time",
                "Appointment time must be in the future.",
            )

        return cleaned_data