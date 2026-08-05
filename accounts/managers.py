# custom file

from django.contrib.auth.models import UserManager


class CustomUserManager(UserManager):
    """
    Custom manager for the CustomUser model.
    Future custom user creation logic can be added here.
    """
    pass