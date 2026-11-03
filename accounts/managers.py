# custom file

from django.contrib.auth.models import UserManager

from .choices import UserRole


class CustomUserManager(UserManager):
    """
    Custom manager for the CustomUser model.
    Future custom user creation logic can be added here.
    """
    def create_superuser(self, username, email=None, password=None, **extra_fields):
        extra_fields.setdefault("role", UserRole.ADMIN)
        return super().create_superuser(
            username,
            email=email,
            password=password,
            **extra_fields,
        )