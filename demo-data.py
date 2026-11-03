from datetime import date, time, timedelta
from decimal import Decimal

from django.utils import timezone

from accounts.models import User
from appointments.models import Appointment
from billing.models import Billing, Payment
from core.models import Notification
from doctors.models import Doctor, DoctorLeave, DoctorSchedule
from patients.models import Patient
from prescriptions.models import Prescription, PrescriptionMedicine
from receptionist.models import Receptionist
from security_audit.models import AuditLog


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
    "users": 0,
    "doctors": 0,
    "receptionists": 0,
    "patients": 0,
    "schedules": 0,
    "doctor_leaves": 0,
    "appointments": 0,
    "prescriptions": 0,
    "prescription_medicines": 0,
    "billings": 0,
    "payments": 0,
    "notifications": 0,
    "audit_logs": 0,
}

# 1. Doctors and doctor profiles
doctor_objects = []
for item in doctors_data:
    user, user_created = get_or_create_user(
        email=item["email"], username=item["username"],
        first_name=item["first_name"], last_name=item["last_name"],
        phone_number=item["phone_number"], role="DOCTOR",
    )
    created_counts["users"] += int(user_created)
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
    user, user_created = get_or_create_user(
        email=email, username=username, first_name=first_name,
        last_name=last_name, phone_number=phone_number, role="RECEPTIONIST",
    )
    created_counts["users"] += int(user_created)
    _, created = Receptionist.objects.get_or_create(
        user=user,
        defaults={"joining_date": date.today()},
    )
    created_counts["receptionists"] += int(created)

# 3. Patients and patient profiles
patient_objects = []
for item in patients_data:
    user, user_created = get_or_create_user(
        email=item["email"], username=item["username"],
        first_name=item["first_name"], last_name=item["last_name"],
        phone_number=item["phone_number"], role="PATIENT",
    )
    created_counts["users"] += int(user_created)
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

# 4. Two weekday schedules for every demo doctor.
schedule_start = time(9, 0)
schedule_end = time(17, 0)
schedule_weekdays = [
    (doctor, (index % 5, (index + 2) % 5))
    for index, doctor in enumerate(doctor_objects)
]
for doctor, weekdays in schedule_weekdays:
    for weekday in weekdays:
        _, created = DoctorSchedule.objects.get_or_create(
            doctor=doctor,
            weekday=weekday,
            start_time=schedule_start,
            defaults={"end_time": schedule_end, "is_active": True},
        )
        created_counts["schedules"] += int(created)

# 5. One upcoming appointment for each demo patient/doctor pair.
today = timezone.localdate()
appointment_reasons = [
    "General health check-up",
    "Heart health consultation",
    "Skin consultation",
    "Child health consultation",
    "Joint pain consultation",
]
for index, (patient, doctor) in enumerate(zip(patient_objects, doctor_objects)):
    appointment_date = today + timedelta(days=index + 1)
    while appointment_date.weekday() not in schedule_weekdays[index][1]:
        appointment_date += timedelta(days=1)
    appointment_time = time(10 + index, 0)
    reason = appointment_reasons[index]

    appointment, created = Appointment.objects.get_or_create(
        patient=patient,
        doctor=doctor,
        reason_for_visit=reason,
        defaults={
            "appointment_date": appointment_date,
            "appointment_time": appointment_time,
            "status": "CONFIRMED",
        },
    )
    created_counts["appointments"] += int(created)

# 6. Record five completed visits so clinical and billing screens have history.
completed_appointments = []
for index, (patient, doctor) in enumerate(zip(patient_objects, doctor_objects)):
    appointment_date = today - timedelta(days=index + 1)
    while appointment_date.weekday() not in schedule_weekdays[index][1]:
        appointment_date -= timedelta(days=1)

    reason = f"Demo follow-up visit {index + 1}"
    appointment, created = Appointment.objects.get_or_create(
        patient=patient,
        doctor=doctor,
        reason_for_visit=reason,
        defaults={
            "appointment_date": appointment_date,
            "appointment_time": time(10 + index, 0),
            "status": "COMPLETED",
        },
    )
    created_counts["appointments"] += int(created)
    completed_appointments.append((patient, doctor, appointment))

# 7. Add five doctor leave dates.
for index, doctor in enumerate(doctor_objects):
    leave_date = today + timedelta(days=7 + index)
    while leave_date.weekday() >= 5:
        leave_date += timedelta(days=1)

    reason = f"Demo leave: personal appointment {index + 1}"
    _, created = DoctorLeave.objects.get_or_create(
        doctor=doctor,
        reason=reason,
        defaults={"leave_date": leave_date, "is_active": True},
    )
    created_counts["doctor_leaves"] += int(created)

# 8. Add prescriptions and two medicine entries for each completed visit.
prescription_data = [
    {
        "diagnosis": "Seasonal allergic rhinitis",
        "remarks": "Demo scenario only; not medical advice.",
        "medicines": [
            ("Demo medication A", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
            ("Demo medication B", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
        ],
    },
    {
        "diagnosis": "Essential hypertension, stable",
        "remarks": "Demo scenario only; not medical advice.",
        "medicines": [
            ("Demo medication C", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
            ("Demo medication D", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
        ],
    },
    {
        "diagnosis": "Mild acne",
        "remarks": "Demo scenario only; not medical advice.",
        "medicines": [
            ("Demo medication E", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
            ("Demo medication F", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
        ],
    },
    {
        "diagnosis": "Viral upper respiratory infection",
        "remarks": "Demo scenario only; not medical advice.",
        "medicines": [
            ("Demo medication G", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
            ("Demo medication H", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
        ],
    },
    {
        "diagnosis": "Mechanical lower-back pain",
        "remarks": "Demo scenario only; not medical advice.",
        "medicines": [
            ("Demo medication I", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
            ("Demo medication J", "Sample dose", "Sample frequency", "Sample duration", "Placeholder only; not a real prescription."),
        ],
    },
]

completed_records = []
for index, (patient, doctor, appointment) in enumerate(completed_appointments):
    item = prescription_data[index]
    prescription, created = Prescription.objects.get_or_create(
        appointment=appointment,
        defaults={
            "diagnosis": item["diagnosis"],
            "remarks": item["remarks"],
            "status": "COMPLETED",
        },
    )
    created_counts["prescriptions"] += int(created)
    completed_records.append((patient, doctor, appointment, prescription))

    for medicine_name, dosage, frequency, duration, instructions in item["medicines"]:
        _, created = PrescriptionMedicine.objects.get_or_create(
            prescription=prescription,
            medicine_name=medicine_name,
            defaults={
                "dosage": dosage,
                "frequency": frequency,
                "duration": duration,
                "instructions": instructions,
            },
        )
        created_counts["prescription_medicines"] += int(created)

# 9. Create five bills and five sample payments for completed visits.
payment_statuses = ["PAID", "PAID", "PARTIAL", "PARTIAL", "PENDING"]
for index, (patient, doctor, appointment, _) in enumerate(completed_records):
    amount = doctor.consultation_fee
    tax_type = "GST" if index % 2 == 0 else "EXEMPT"
    tax_amount = (
        (amount * Decimal("0.18")).quantize(Decimal("0.01"))
        if tax_type == "GST"
        else Decimal("0.00")
    )
    bill, created = Billing.objects.get_or_create(
        appointment=appointment,
        defaults={
            "patient": patient,
            "amount": amount,
            "tax_type": tax_type,
            "tax_amount": tax_amount,
            "total_amount": amount + tax_amount,
            "payment_status": payment_statuses[index],
        },
    )
    created_counts["billings"] += int(created)

    total = bill.total_amount
    if index in (0, 1):
        payment_parts = [(total, "CARD" if index == 0 else "UPI", "FINAL")]
    elif index == 2:
        advance = (total / 2).quantize(Decimal("0.01"))
        payment_parts = [
            (advance, "CASH", "ADVANCE"),
            (total - advance, "UPI", "FINAL"),
        ]
    elif index == 3:
        payment_parts = [
            ((total / 2).quantize(Decimal("0.01")), "CARD", "PARTIAL"),
        ]
    else:
        payment_parts = []

    for payment_index, (payment_amount, method, payment_type) in enumerate(payment_parts):
        _, created = Payment.objects.get_or_create(
            billing=bill,
            transaction_reference=f"DEMO-PAY-{index + 1}-{payment_index + 1}",
            defaults={
                "amount": payment_amount,
                "payment_method": method,
                "payment_type": payment_type,
            },
        )
        created_counts["payments"] += int(created)

# 10. Seed notifications and audit entries for the completed visits.
for index, (patient, doctor, appointment, _) in enumerate(completed_records):
    message = f"Demo appointment {appointment.appointment_id} was completed."
    _, created = Notification.objects.get_or_create(
        recipient=patient.user,
        message=message,
        target_url="/dashboard/",
        defaults={"actor_name": doctor.user.get_full_name()},
    )
    created_counts["notifications"] += int(created)

    _, created = AuditLog.objects.get_or_create(
        actor=doctor.user,
        action="DEMO_APPOINTMENT_COMPLETED",
        target_user=patient.user,
        target_identifier=appointment.appointment_id,
        outcome=AuditLog.Outcome.SUCCESS,
        defaults={
            "ip_address": f"192.0.2.{index + 1}",
            "user_agent": "SHMS demo-data seed",
            "details": {"source": "demo-data.py"},
        },
    )
    created_counts["audit_logs"] += int(created)

print("\n========== SHMS DEMO DATA SUMMARY ==========")
print("New demo user accounts created:", created_counts["users"])
print("New doctor profiles created:", created_counts["doctors"])
print("New receptionist profiles created:", created_counts["receptionists"])
print("New patient profiles created:", created_counts["patients"])
print("New doctor schedules created:", created_counts["schedules"])
print("New doctor leaves created:", created_counts["doctor_leaves"])
print("New appointments created:", created_counts["appointments"])
print("New prescriptions created:", created_counts["prescriptions"])
print("New prescription medicines created:", created_counts["prescription_medicines"])
print("New bills created:", created_counts["billings"])
print("New payments created:", created_counts["payments"])
print("New notifications created:", created_counts["notifications"])
print("New audit logs created:", created_counts["audit_logs"])
print("\nTotal records currently in database:")
print("Users:", User.objects.count())
print("Doctors:", Doctor.objects.count())
print("Receptionists:", Receptionist.objects.count())
print("Patients:", Patient.objects.count())
print("Doctor schedules:", DoctorSchedule.objects.count())
print("Doctor leaves:", DoctorLeave.objects.count())
print("Appointments:", Appointment.objects.count())
print("Prescriptions:", Prescription.objects.count())
print("Prescription medicines:", PrescriptionMedicine.objects.count())
print("Billings:", Billing.objects.count())
print("Payments:", Payment.objects.count())
print("Notifications:", Notification.objects.count())
print("Audit logs:", AuditLog.objects.count())
print("\nDemo login password for newly created users:", DEMO_PASSWORD)
print("Demo emails use the format demo.<role><number>@shms.test")
print("============================================\n")
