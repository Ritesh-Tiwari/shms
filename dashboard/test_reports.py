import csv
from datetime import date, time, timedelta
from decimal import Decimal
from io import StringIO

from django.test import TestCase
from django.urls import reverse

from accounts.choices import UserRole
from accounts.models import User
from appointments.models import Appointment, AppointmentStatus
from billing.models import Billing, Payment, PaymentMethod, PaymentType
from doctors.choices import SpecializationChoices, Weekday
from doctors.models import Doctor, DoctorSchedule
from patients.choices import BloodGroupChoices, GenderChoices
from patients.models import Patient
from prescriptions.models import Prescription, PrescriptionMedicine


class ReportingWorkflowTests(TestCase):
    def setUp(self):
        self.admin = User.objects.create_user(
            username="reports-admin",
            email="reports-admin@example.com",
            password="test-password",
            role=UserRole.ADMIN,
        )
        self.patient_user = User.objects.create_user(
            username="reports-patient",
            email="reports-patient@example.com",
            password="test-password",
            role=UserRole.PATIENT,
            first_name="Report",
            last_name="Patient",
            phone_number="9876543210",
        )
        self.doctor_user = User.objects.create_user(
            username="reports-doctor",
            email="reports-doctor@example.com",
            password="test-password",
            role=UserRole.DOCTOR,
            first_name="Report",
            last_name="Doctor",
        )
        self.patient = Patient.objects.create(
            user=self.patient_user,
            date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE,
            blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210",
            address="Test Road",
            city="Kolkata",
            state="West Bengal",
            pincode="700001",
        )
        self.doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=4,
            consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        DoctorSchedule.objects.create(
            doctor=self.doctor,
            weekday=Weekday.MONDAY,
            start_time=time(9, 0),
            end_time=time(12, 0),
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today(),
            appointment_time=time(10, 0),
            reason_for_visit="Check-up",
            status=AppointmentStatus.COMPLETED,
        )
        self.prescription = Prescription.objects.create(
            appointment=self.appointment,
            diagnosis="Seasonal allergies",
        )
        PrescriptionMedicine.objects.create(
            prescription=self.prescription,
            medicine_name="Cetirizine",
            dosage="10 mg",
            frequency="Once daily",
            duration="5 days",
        )
        self.billing = Billing.objects.create(
            appointment=self.appointment,
            patient=self.patient,
            amount=Decimal("500.00"),
            tax_amount=Decimal("90.00"),
            total_amount=Decimal("590.00"),
        )
        Payment.objects.create(
            billing=self.billing,
            amount=Decimal("200.00"),
            payment_method=PaymentMethod.UPI,
            payment_type=PaymentType.ADVANCE,
            transaction_reference="REPORT-TXN-001",
        )
        self.client.force_login(self.admin)

    def test_admin_can_generate_all_proposal_reports(self):
        reports = {
            "patients": "Patient Registration Report",
            "appointments": "Appointment Summary Report",
            "doctor_schedules": "Doctor Schedule Report",
            "prescriptions": "Prescription Report",
            "billing_revenue": "Billing &amp; Revenue Report",
            "payment_status": "Payment Status Report",
        }

        for report_key, title in reports.items():
            with self.subTest(report=report_key):
                response = self.client.get(
                    reverse("dashboard:reports"),
                    {"report": report_key},
                )
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, title)
                self.assertEqual(response.context["page_obj"].paginator.count, 1)

    def test_each_report_can_be_exported_as_csv(self):
        expected_headers = {
            "patients": (
                "Patient ID,Patient Name,Email,Phone,Date of Birth,Gender,"
                "City,Registered On"
            ),
            "appointments": (
                "Appointment ID,Patient,Doctor,Date,Time,Status,Reason"
            ),
            "doctor_schedules": (
                "Doctor ID,Doctor,Specialization,Availability,Weekday,"
                "Start Time,End Time,Schedule Status"
            ),
            "prescriptions": (
                "Prescription ID,Appointment ID,Patient,Doctor,Diagnosis,"
                "Medicines,Status,Created On"
            ),
            "billing_revenue": (
                "Bill ID,Appointment ID,Patient,Doctor,Bill Date,Amount,Tax,"
                "Total,Payment Status"
            ),
            "payment_status": (
                "Payment ID,Transaction Reference,Bill ID,Patient,"
                "Payment Method,Payment Amount,Payment Date,Bill Status,"
                "Outstanding"
            ),
        }

        for report_key, header in expected_headers.items():
            with self.subTest(report=report_key):
                response = self.client.get(
                    reverse("dashboard:report-download"),
                    {"report": report_key},
                )
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "text/csv; charset=utf-8")
                self.assertIn(header, response.content.decode("utf-8"))
                self.assertIn("attachment;", response["Content-Disposition"])

    def test_payment_status_report_shows_partial_and_unpaid_bills(self):
        Payment.objects.create(
            billing=self.billing,
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.CASH,
            payment_type=PaymentType.PARTIAL,
        )
        unpaid_appointment = Appointment.objects.create(
            patient=self.patient,
            doctor=self.doctor,
            appointment_date=date.today(),
            appointment_time=time(11, 0),
            reason_for_visit="Follow-up",
            status=AppointmentStatus.COMPLETED,
        )
        unpaid_bill = Billing.objects.create(
            appointment=unpaid_appointment,
            patient=self.patient,
            amount=Decimal("500.00"),
            tax_amount=Decimal("90.00"),
            total_amount=Decimal("590.00"),
        )

        response = self.client.get(
            reverse("dashboard:report-download"),
            {"report": "payment_status"},
        )
        rows = list(csv.reader(StringIO(response.content.decode("utf-8"))))
        headers = rows[0]
        outstanding_index = headers.index("Outstanding")
        bill_id_index = headers.index("Bill ID")
        payment_id_index = headers.index("Payment ID")

        partial_rows = [
            row for row in rows[1:] if row[bill_id_index] == self.billing.bill_id
        ]
        unpaid_rows = [
            row for row in rows[1:] if row[bill_id_index] == unpaid_bill.bill_id
        ]

        self.assertEqual(len(partial_rows), 2)
        self.assertTrue(
            all(row[outstanding_index] == "290.00" for row in partial_rows)
        )
        self.assertEqual(len(unpaid_rows), 1)
        self.assertEqual(unpaid_rows[0][payment_id_index], "")
        self.assertEqual(unpaid_rows[0][outstanding_index], "590.00")

    def test_date_range_filters_reports_and_preserves_filter_in_download(self):
        response = self.client.get(
            reverse("dashboard:reports"),
            {
                "report": "appointments",
                "start_date": (date.today() + timedelta(days=1)).isoformat(),
                "end_date": (date.today() + timedelta(days=2)).isoformat(),
            },
        )
        self.assertEqual(response.context["page_obj"].paginator.count, 0)

        response = self.client.get(
            reverse("dashboard:report-download"),
            {
                "report": "appointments",
                "start_date": date.today().isoformat(),
                "end_date": date.today().isoformat(),
            },
        )
        self.assertIn(self.appointment.appointment_id, response.content.decode())

    def test_invalid_date_range_is_rejected_for_page_and_download(self):
        params = {
            "report": "patients",
            "start_date": date.today().isoformat(),
            "end_date": (date.today() - timedelta(days=1)).isoformat(),
        }
        response = self.client.get(reverse("dashboard:reports"), params)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "start date must be on or before")

        response = self.client.get(reverse("dashboard:report-download"), params)
        self.assertEqual(response.status_code, 400)

    def test_non_admin_cannot_view_or_download_reports(self):
        self.client.force_login(self.patient_user)
        for url_name in ("dashboard:reports", "dashboard:report-download"):
            with self.subTest(url=url_name):
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 403)

    def test_csv_export_escapes_spreadsheet_formulas(self):
        self.patient_user.first_name = "=1+1"
        self.patient_user.save(update_fields=["first_name"])

        response = self.client.get(
            reverse("dashboard:report-download"),
            {"report": "patients"},
        )

        self.assertIn("'=1+1", response.content.decode("utf-8"))
