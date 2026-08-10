from django import forms
from django.forms import inlineformset_factory


from .models import Prescription, PrescriptionMedicine


class PrescriptionForm(forms.ModelForm):

    class Meta:

        model = Prescription

        fields = [
            "diagnosis",
            "remarks",
        ]

        widgets = {

            "diagnosis": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Enter diagnosis",
                }
            ),

            "remarks": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Additional remarks",
                }
            ),
        }


class PrescriptionMedicineForm(forms.ModelForm):

    class Meta:

        model = PrescriptionMedicine

        fields = [
            "medicine_name",
            "dosage",
            "frequency",
            "duration",
            "instructions",
        ]

        widgets = {

            "medicine_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Medicine name",
                }
            ),

            "dosage": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 500 mg",
                }
            ),

            "frequency": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 2 times/day",
                }
            ),

            "duration": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "e.g. 5 days",
                }
            ),

            "instructions": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 2,
                    "placeholder": "e.g. After food",
                }
            ),
        }

PrescriptionMedicineFormSet = inlineformset_factory(
    Prescription,
    PrescriptionMedicine,
    form=PrescriptionMedicineForm,
    extra=1,
    can_delete=True,
)