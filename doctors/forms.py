from django import forms

from .models import Doctor


class DoctorForm(forms.ModelForm):

    class Meta:

        model = Doctor

        exclude = (
            "user",
            "doctor_id",
            "created_at",
            "updated_at",
        )