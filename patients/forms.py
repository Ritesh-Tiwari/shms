from django import forms

from .models import Patient


class PatientForm(forms.ModelForm):

    class Meta:

        model = Patient

        exclude = [
            "user",
            "patient_id",
            "created_at",
            "updated_at",
        ]

        widgets = {

            "date_of_birth": forms.DateInput(
                attrs={
                    "type": "date",
                },
            ),

            "address": forms.Textarea(
                attrs={
                    "rows": 3,
                },
            ),

            "allergies": forms.Textarea(
                attrs={
                    "rows": 3,
                },
            ),

            "medical_history": forms.Textarea(
                attrs={
                    "rows": 3,
                },
            ),

        }