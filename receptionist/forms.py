from django import forms
from django.contrib.auth.password_validation import (
    validate_password,
)

from accounts.models import User
from appointments.models import Appointment
from .models import Receptionist


class ReceptionistUserForm(forms.ModelForm):

    password = forms.CharField(
        required=False,
        strip=False,
        widget=forms.PasswordInput(
            attrs={
                "placeholder": "Enter password",
                "autocomplete": "new-password",
            }
        ),
    )

    class Meta:

        model = User

        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "phone_number",
            "password",
        ]

        widgets = {

            "username": forms.TextInput(
                attrs={
                    "placeholder": "Enter username",
                }
            ),

            "first_name": forms.TextInput(
                attrs={
                    "placeholder": "First name",
                }
            ),

            "last_name": forms.TextInput(
                attrs={
                    "placeholder": "Last name",
                }
            ),

            "email": forms.EmailInput(
                attrs={
                    "placeholder": "Enter email address",
                }
            ),

            "phone_number": forms.TextInput(
                attrs={
                    "placeholder": "+91 XXXXX XXXXX",
                    "maxlength": "15",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields["password"].required = (
            self.instance.pk is None
        )

        for field in self.fields.values():

            field.widget.attrs.update({
                "class": (
                    "w-full rounded-lg border "
                    "border-slate-300 bg-white "
                    "px-4 py-3 text-sm "
                    "focus:outline-none "
                    "focus:ring-2 "
                    "focus:ring-blue-500"
                )
            })

    def clean_email(self):

        email = self.cleaned_data.get(
            "email",
            "",
        ).strip().lower()

        return email

    def clean_password(self):

        password = self.cleaned_data.get(
            "password"
        )

        if password:

            validate_password(
                password,
                user=self.instance
                if self.instance.pk
                else None,
            )

        return password


class ReceptionistProfileForm(forms.ModelForm):

    class Meta:

        model = Receptionist

        fields = [
            "joining_date",
        ]

        widgets = {

            "joining_date": forms.DateInput(
                attrs={
                    "type": "date",
                    "class": (
                        "w-full rounded-lg border "
                        "border-slate-300 bg-white "
                        "px-4 py-3 text-sm "
                        "focus:outline-none "
                        "focus:ring-2 "
                        "focus:ring-blue-500"
                    ),
                }
            ),
        }

class AppointmentSearchForm(forms.Form):

    search = forms.CharField(
        required=False,
        max_length=100,
        strip=True,
    )

    appointment_date = forms.DateField(
        required=False,
        widget=forms.DateInput(
            attrs={
                "type": "date",
            }
        ),
    )

    status = forms.ChoiceField(
        required=False,
        choices=[
            ("", "All statuses"),
            *Appointment._meta.get_field(
                "status"
            ).choices,
        ],
    )

    def clean_search(self):
        search = self.cleaned_data.get(
            "search",
            "",
        )

        return search.strip()