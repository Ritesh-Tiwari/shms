from django.db import transaction

from accounts.models import User
from .models import Patient


class PatientRegistrationService:

    @staticmethod
    @transaction.atomic
    def register():
        pass