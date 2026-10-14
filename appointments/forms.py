from django import forms

from doctors.models import Doctor

from .availability import get_booking_error
from .models import Appointment


class AvailableDoctorFormMixin:

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if "doctor" in self.fields:

            self.fields["doctor"].queryset = (
                Doctor.objects
                .filter(
                    user__is_active=True,
                    availability="AVAILABLE",
                )
                .select_related("user")
                .order_by("doctor_id")
            )


class AppointmentValidationMixin:

    def validate_appointment_slot(
        self,
        doctor,
        appointment_date,
        appointment_time,
    ):

        exclude_appointment_id = None

        if self.instance and self.instance.pk:
            exclude_appointment_id = self.instance.pk

        error = get_booking_error(
            doctor=doctor,
            appointment_date=appointment_date,
            appointment_time=appointment_time,
            exclude_appointment_id=exclude_appointment_id,
        )

        if error:
            field_name, error_message = error

            self.add_error(
                field_name,
                error_message,
            )


class AppointmentForm(
    AvailableDoctorFormMixin,
    AppointmentValidationMixin,
    forms.ModelForm,
):

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
            "appointment_date": forms.Select(),
            "appointment_time": forms.Select(),
            "reason_for_visit": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": 255,
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        self.validate_appointment_slot(
            doctor=cleaned_data.get("doctor"),
            appointment_date=cleaned_data.get("appointment_date"),
            appointment_time=cleaned_data.get("appointment_time"),
        )

        return cleaned_data


class PatientAppointmentForm(
    AvailableDoctorFormMixin,
    AppointmentValidationMixin,
    forms.ModelForm,
):

    class Meta:

        model = Appointment

        fields = [
            "doctor",
            "appointment_date",
            "appointment_time",
            "reason_for_visit",
        ]

        widgets = {
            "appointment_date": forms.Select(),
            "appointment_time": forms.Select(),
            "reason_for_visit": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": 255,
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        self.validate_appointment_slot(
            doctor=cleaned_data.get("doctor"),
            appointment_date=cleaned_data.get("appointment_date"),
            appointment_time=cleaned_data.get("appointment_time"),
        )

        return cleaned_data


class AppointmentUpdateForm(
    AppointmentValidationMixin,
    forms.ModelForm,
):

    class Meta:

        model = Appointment

        fields = [
            "appointment_date",
            "appointment_time",
            "reason_for_visit",
        ]

        widgets = {
            "appointment_date": forms.Select(),
            "appointment_time": forms.Select(),
            "reason_for_visit": forms.Textarea(
                attrs={
                    "rows": 3,
                    "maxlength": 255,
                }
            ),
        }

    def clean(self):

        cleaned_data = super().clean()

        self.validate_appointment_slot(
            doctor=self.instance.doctor,
            appointment_date=cleaned_data.get("appointment_date"),
            appointment_time=cleaned_data.get("appointment_time"),
        )

        return cleaned_data