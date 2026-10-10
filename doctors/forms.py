from django import forms
from .models import Doctor, DoctorSchedule


class DoctorForm(forms.ModelForm):
 
    class Meta:

        model = Doctor

        exclude = (
            "user",
            "doctor_id",
            "created_at",
            "updated_at",
        )

        widgets = {

            
        }

class DoctorScheduleForm(forms.ModelForm):

    class Meta:
        model = DoctorSchedule
        fields = [
            "weekday",
            "start_time",
            "end_time",
            "is_active",
        ]

        widgets = {
            "start_time": forms.TimeInput(
                attrs={"type": "time"}
            ),
            "end_time": forms.TimeInput(
                attrs={"type": "time"}
            ),
        }

    def clean(self):
        cleaned_data = super().clean()

        start_time = cleaned_data.get("start_time")
        end_time = cleaned_data.get("end_time")

        if start_time and end_time and start_time >= end_time:
            self.add_error(
                "end_time",
                "End time must be later than start time.",
            )

        return cleaned_data