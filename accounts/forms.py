from django import forms

from .models import User


class UserRegistrationForm(forms.ModelForm):

    password = forms.CharField(
        widget=forms.PasswordInput(),
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