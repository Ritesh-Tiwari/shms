from django import forms

from .models import Appointment


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