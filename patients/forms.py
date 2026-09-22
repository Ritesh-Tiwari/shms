from django import forms

from patients.choices import GenderChoices, BloodGroupChoices

from .models import Patient

class DisabledPlaceholderSelect(forms.Select):

    def create_option(
        self,
        name,
        value,
        label,
        selected,
        index,
        subindex=None,
        attrs=None,
    ):
        option = super().create_option(
            name,
            value,
            label,
            selected,
            index,
            subindex,
            attrs,
        )

        if value == "":
            option["attrs"]["disabled"] = True

        return option

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
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all appearance-none",
                    "id": "dob",
                    "required": True,
                },
            ),

            "gender": DisabledPlaceholderSelect(
                attrs={
                    "class": (
                        "w-full bg-surface h-12 px-md rounded-lg "
                        "text-body-md text-on-surface "
                        "focus:outline-none focus:ring-2 "
                        "focus:ring-primary/20 transition-all "
                        "appearance-none"
                    ),
                    "id": "gender",
                    "required": True,
                },
            ),

            "blood_group": DisabledPlaceholderSelect(
                attrs={
                    "class": (
                        "w-full bg-surface h-12 px-md rounded-lg "
                        "text-body-md text-on-surface "
                        "focus:outline-none focus:ring-2 "
                        "focus:ring-primary/20 transition-all "
                        "appearance-none"
                    ),
                    "id": "bloodGroup",
                    'required': True,
                },
            ),

            "emergency_contact": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "name & phone number",
                    "id": "emergencyContact",
                    "type": "tel",
                },
            ),

            "address": forms.Textarea(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "123 Main St, Apt 4B",
                    "id": "address",
                    "type": "text",
                },
            ),

            "city": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "banaras",
                    "id": "city",
                    "type": "text",
                },
            ),

            "state": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "Uttar Pradesh",
                    "id": "state",
                    "type": "text",
                },
            ),

            "pincode": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "221001",
                    "id": "pincode",
                    "maxlength": "10",
                    "type": "text",
                },
            ),

            "allergies": forms.Textarea(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "List any drug, food, or environmental allergies...",
                    "id": "allergies",
                    "rows": "3",
                },
            ),

            "medical_history": forms.Textarea(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "Chronic conditions, past surgeries, or family history notes...",
                    "id": "medicalHistory",
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["gender"].choices = [
            ("", "Select gender"),
            *GenderChoices.choices,
        ]

        self.fields["blood_group"].choices = [
            ("", "Select type"),
            *BloodGroupChoices.choices,
        ]