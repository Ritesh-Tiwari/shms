from accounts.models import User
from accounts.choices import UserRole

from .models import Doctor


class DoctorService:

    @staticmethod
    def create_doctor(
        user_data,
        doctor_data,
    ):

        user = User.objects.create_user(
            username=user_data["username"],
            email=user_data["email"],
            password=user_data["password"],
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            role=UserRole.DOCTOR,
            phone_number=user_data["phone_number"],
        )

        doctor = Doctor.objects.create(
            user=user,
            **doctor_data,
        )

        return doctor

    @staticmethod
    def update_doctor(
        doctor,
        user_data,
        doctor_data,
    ):

        user = doctor.user

        user.first_name = user_data["first_name"]
        user.last_name = user_data["last_name"]
        user.email = user_data["email"]
        user.phone_number = user_data["phone_number"]

        password = user_data.get("password")

        if password:
            user.set_password(password)

        user.save()

        for field, value in doctor_data.items():
            setattr(
                doctor,
                field,
                value,
            )

        doctor.save()

        return doctor