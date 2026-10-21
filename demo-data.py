from datetime import date, time, timedelta

from django.utils import timezone

from accounts.models import User
from doctors.models import Doctor, DoctorSchedule
from receptionist.models import Receptionist
from patients.models import Patient
from appointments.models import Appointment


DEMO_PASSWORD = "Demo@12345"

doctors_data = [
    {
        "email": "demo.doctor1@shms.test", "username": "demo_doctor1",
        "first_name": "Aarav", "last_name": "Sharma", "phone_number": "9000000101",
        "specialization": "GENERAL_PHYSICIAN", "qualification": "MBBS",
        "experience": 5, "consultation_fee": 500, "availability": "AVAILABLE",
        "address": "Clinic Room 101",
    },
    {
        "email": "demo.doctor2@shms.test", "username": "demo_doctor2",
        "first_name": "Diya", "last_name": "Verma", "phone_number": "9000000102",
        "specialization": "CARDIOLOGIST", "qualification": "MBBS, MD Cardiology",
        "experience": 8, "consultation_fee": 800, "availability": "AVAILABLE",
        "address": "Clinic Room 102",
    },
    {
        "email": "demo.doctor3@shms.test", "username": "demo_doctor3",
        "first_name": "Kabir", "last_name": "Singh", "phone_number": "9000000103",
        "specialization": "DERMATOLOGIST", "qualification": "MBBS, MD Dermatology",
        "experience": 6, "consultation_fee": 650, "availability": "AVAILABLE",
        "address": "Clinic Room 103",
    },
    {
        "email": "demo.doctor4@shms.test", "username": "demo_doctor4",
        "first_name": "Ananya", "last_name": "Das", "phone_number": "9000000104",
        "specialization": "PEDIATRICIAN", "qualification": "MBBS, MD Pediatrics",
        "experience": 7, "consultation_fee": 600, "availability": "AVAILABLE",
        "address": "Clinic Room 104",
    },
    {
        "email": "demo.doctor5@shms.test", "username": "demo_doctor5",
        "first_name": "Ishaan", "last_name": "Roy", "phone_number": "9000000105",
        "specialization": "ORTHOPEDIC", "qualification": "MBBS, MS Orthopedics",
        "experience": 9, "consultation_fee": 750, "availability": "AVAILABLE",
        "address": "Clinic Room 105",
    },
]

receptionists_data = [
    ("demo.receptionist1@shms.test", "demo_receptionist1", "Riya", "Sen", "9000000201"),
    ("demo.receptionist2@shms.test", "demo_receptionist2", "Arjun", "Paul", "9000000202"),
    ("demo.receptionist3@shms.test", "demo_receptionist3", "Meera", "Ghosh", "9000000203"),
    ("demo.receptionist4@shms.test", "demo_receptionist4", "Rahul", "Dey", "9000000204"),
    ("demo.receptionist5@shms.test", "demo_receptionist5", "Priya", "Bose", "9000000205"),
]

patients_data = [
    {
        "email": "demo.patient1@shms.test", "username": "demo_patient1",
        "first_name": "Aditya", "last_name": "Kumar", "phone_number": "9000000301",
        "date_of_birth": date(1995, 4, 12), "gender": "MALE", "blood_group": "O+",
        "emergency_contact": "9000000401", "address": "12 Lake Road",
        "city": "Kolkata", "state": "West Bengal", "pincode": "700029",
        "allergies": "None known", "medical_history": "No major medical history",
    },
    {
        "email": "demo.patient2@shms.test", "username": "demo_patient2",
        "first_name": "Sneha", "last_name": "Patel", "phone_number": "9000000302",
        "date_of_birth": date(1992, 8, 21), "gender": "FEMALE", "blood_group": "A+",
        "emergency_contact": "9000000402", "address": "25 Park Street",
        "city": "Kolkata", "state": "West Bengal", "pincode": "700016",
        "allergies": "None known", "medical_history": "Seasonal allergies",
    },
    {
        "email": "demo.patient3@shms.test", "username": "demo_patient3",
        "first_name": "Rahul", "last_name": "Mitra", "phone_number": "9000000303",
        "date_of_birth": date(1988, 2, 5), "gender": "MALE", "blood_group": "B+",
        "emergency_contact": "9000000403", "address": "8 Salt Lake",
        "city": "Kolkata", "state": "West Bengal", "pincode": "700091",
        "allergies": "None known", "medical_history": "Mild asthma",
    },
    {
        "email": "demo.patient4@shms.test", "username": "demo_patient4",
        "first_name": "Pooja", "last_name": "Nair", "phone_number": "9000000304",
        "date_of_birth": date(2000, 11, 17), "gender": "FEMALE", "blood_group": "AB+",
        "emergency_contact": "9000000404", "address": "14 New Town",
        "city": "Kolkata", "state": "West Bengal", "pincode": "700156",
        "allergies": "None known", "medical_history": "No major medical history",
    },
    {
        "email": "demo.patient5@shms.test", "username": "demo_patient5",
        "first_name": "Sourav", "last_name": "Chatterjee", "phone_number": "9000000305",
        "date_of_birth": date(1997, 6, 30), "gender": "MALE", "blood_group": "A-",
        "emergency_contact": "9000000405", "address": "31 Howrah Road",
        "city": "Howrah", "state": "West Bengal", "pincode": "711101",
        "allergies": "None known", "medical_history": "No major medical history",
    },
]


def get_or_create_user(*, email, username, first_name, last_name, phone_number, role):
    user, created = User.objects.get_or_create(
        email=email,
        defaults={
            "username": username,
            "first_name": first_name,
            "last_name": last_name,
            "phone_number": phone_number,
            "role": role,
        },
    )
    if created:
        user.set_password(DEMO_PASSWORD)
        user.save()
    return user, created


created_counts = {
    "doctors": 0,
    "receptionists": 0,
    "patients": 0,
    "schedules": 0,
    "appointments": 0,
}

# 1. Doctors and doctor profiles
doctor_objects = []
for item in doctors_data:
    user, _ = get_or_create_user(
        email=item["email"], username=item["username"],
        first_name=item["first_name"], last_name=item["last_name"],
        phone_number=item["phone_number"], role="DOCTOR",
    )
    profile, created = Doctor.objects.get_or_create(
        user=user,
        defaults={
            "specialization": item["specialization"],
            "qualification": item["qualification"],
            "experience": item["experience"],
            "consultation_fee": item["consultation_fee"],
            "availability": item["availability"],
            "address": item["address"],
        },
    )
    created_counts["doctors"] += int(created)
    doctor_objects.append(profile)

# 2. Receptionists and receptionist profiles
for email, username, first_name, last_name, phone_number in receptionists_data:
    user, _ = get_or_create_user(
        email=email, username=username, first_name=first_name,
        last_name=last_name, phone_number=phone_number, role="RECEPTIONIST",
    )
    _, created = Receptionist.objects.get_or_create(
        user=user,
        defaults={"joining_date": date.today()},
    )
    created_counts["receptionists"] += int(created)

# 3. Patients and patient profiles
patient_objects = []
for item in patients_data:
    user, _ = get_or_create_user(
        email=item["email"], username=item["username"],
        first_name=item["first_name"], last_name=item["last_name"],
        phone_number=item["phone_number"], role="PATIENT",
    )
    profile_fields = {
        key: value for key, value in item.items()
        if key not in {"email", "username", "first_name", "last_name", "phone_number"}
    }
    profile, created = Patient.objects.get_or_create(
        user=user,
        defaults=profile_fields,
    )
    created_counts["patients"] += int(created)
    patient_objects.append(profile)

# 4. Weekday schedules (Monday-Friday) for every demo doctor
schedule_start = time(9, 0)
schedule_end = time(17, 0)
for doctor in doctor_objects:
    for weekday in range(5):
        _, created = DoctorSchedule.objects.get_or_create(
            doctor=doctor,
            weekday=weekday,
            start_time=schedule_start,
            defaults={"end_time": schedule_end, "is_active": True},
        )
        created_counts["schedules"] += int(created)

# 5. One future appointment for each demo patient/doctor pair.
# Pick the next Monday-Friday date and a time inside the schedule.
today = timezone.localdate()
for index, (patient, doctor) in enumerate(zip(patient_objects, doctor_objects)):
    appointment_date = today + timedelta(days=1)
    while appointment_date.weekday() >= 5:
        appointment_date += timedelta(days=1)
    appointment_time = time(10 + index, 0)

    # Ensure the date is a weekday; if today/tomorrow logic changes, keep advancing.
    while appointment_date.weekday() >= 5:
        appointment_date += timedelta(days=1)

    _, created = Appointment.objects.get_or_create(
        doctor=doctor,
        appointment_date=appointment_date,
        appointment_time=appointment_time,
        defaults={
            "patient": patient,
            "reason_for_visit": [
                "General health check-up",
                "Heart health consultation",
                "Skin consultation",
                "Child health consultation",
                "Joint pain consultation",
            ][index],
            "status": "CONFIRMED",
        },
    )
    created_counts["appointments"] += int(created)

print("\n========== SHMS DEMO DATA SUMMARY ==========")
print("New doctor profiles created:", created_counts["doctors"])
print("New receptionist profiles created:", created_counts["receptionists"])
print("New patient profiles created:", created_counts["patients"])
print("New doctor schedules created:", created_counts["schedules"])
print("New appointments created:", created_counts["appointments"])
print("\nTotal records currently in database:")
print("Doctors:", Doctor.objects.count())
print("Receptionists:", Receptionist.objects.count())
print("Patients:", Patient.objects.count())
print("Doctor schedules:", DoctorSchedule.objects.count())
print("Appointments:", Appointment.objects.count())
print("\nDemo login password for newly created users:", DEMO_PASSWORD)
print("Demo emails use the format demo.<role><number>@shms.test")
print("============================================\n")
