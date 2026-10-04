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
                    "required": True,
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


class PatientOwnProfileForm(forms.ModelForm):
    """
    Patient self-service profile form.

    Only contact/address fields are editable here. Clinical fields
    remain staff-managed.
    """

    class Meta:
        model = Patient
        fields = [
            "emergency_contact",
            "address",
            "city",
            "state",
            "pincode",
        ]
        widgets = {
            "emergency_contact": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "name & phone number",
                    "id": "emergencyContact",
                    "type": "tel",
                    "maxlength": "15",
                    "autocomplete": "tel",
                },
            ),
            "address": forms.Textarea(
                attrs={
                    "class": "w-full bg-surface min-h-24 p-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "123 Main St, Apt 4B",
                    "id": "address",
                    "rows": "3",
                },
            ),
            "city": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "City",
                    "id": "city",
                    "type": "text",
                    "autocomplete": "address-level2",
                },
            ),
            "state": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "State",
                    "id": "state",
                    "type": "text",
                    "autocomplete": "address-level1",
                },
            ),
            "pincode": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "Pincode",
                    "id": "pincode",
                    "maxlength": "10",
                    "type": "text",
                    "inputmode": "numeric",
                    "autocomplete": "postal-code",
                },
            ),
        }

    def clean_emergency_contact(self):
        value = self.cleaned_data["emergency_contact"].strip()
        if not value:
            raise forms.ValidationError("Emergency contact is required.")
        return value

    def clean_address(self):
        value = self.cleaned_data["address"].strip()
        if not value:
            raise forms.ValidationError("Address is required.")
        return value

    def clean_city(self):
        value = self.cleaned_data["city"].strip()
        if not value:
            raise forms.ValidationError("City is required.")
        return value

    def clean_state(self):
        value = self.cleaned_data["state"].strip()
        if not value:
            raise forms.ValidationError("State is required.")
        return value

    def clean_pincode(self):
        value = self.cleaned_data["pincode"].strip()
        if not value:
            raise forms.ValidationError("Pincode is required.")
        if not value.isdigit():
            raise forms.ValidationError("Pincode must contain digits only.")
        if not 4 <= len(value) <= 10:
            raise forms.ValidationError("Pincode must be between 4 and 10 digits.")
        return value
