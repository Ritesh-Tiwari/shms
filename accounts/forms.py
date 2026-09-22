from django import forms

from .models import User


class UserRegistrationForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(
            attrs={
                "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                "placeholder": "••••••••",
                "id": "password",
            },
        ),
        required=False,
        help_text="Leave blank to keep current password.",
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
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "patient.smith",
                    "id": "username",
                    "required": True,
                    "type": "text",
                },
            ),

            "first_name": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "John",
                    "id": "firstName",
                    "required": True,
                    "type": "text",
                },
            ),

            "last_name": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "Doe",
                    "id": "lastName",
                    "required": True,
                    "type": "text",
                },
            ),

            "email": forms.EmailInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "user@example.com",
                    "id": "email",
                    "type": "email",
                },
            ),

            "phone_number": forms.TextInput(
                attrs={
                    "class": "w-full bg-surface h-12 px-md rounded-lg text-body-md text-on-surface focus:outline-none focus:ring-2 focus:ring-primary/20 transition-all",
                    "placeholder": "+91 XXXXX XXXXX",
                    "maxlength": "15",
                    "id": "phone",

                },
            ),
            
        }