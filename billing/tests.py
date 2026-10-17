from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase
from accounts.models import User
from accounts.choices import UserRole
from patients.models import Patient
from patients.choices import GenderChoices, BloodGroupChoices
from doctors.models import Doctor
from doctors.choices import SpecializationChoices
from appointments.models import Appointment, AppointmentStatus
from .models import Billing, Payment, PaymentMethod, PaymentType, PaymentStatus
from .forms import BillingForm, PaymentForm


class BillingModelTests(TestCase):
    def setUp(self):
        patient_user = User.objects.create_user(
            username="billpatient", email="billpatient@example.com",
            password="StrongPassword123!", role=UserRole.PATIENT,
        )
        self.patient = Patient.objects.create(
            user=patient_user, date_of_birth=date(1990, 1, 1),
            gender=GenderChoices.MALE, blood_group=BloodGroupChoices.O_POSITIVE,
            emergency_contact="9876543210", address="Test Road",
            city="Kolkata", state="West Bengal", pincode="700001",
        )
        doctor_user = User.objects.create_user(
            username="billdoctor", email="billdoctor@example.com",
            password="StrongPassword123!", role=UserRole.DOCTOR,
        )
        self.doctor = Doctor.objects.create(
            user=doctor_user, specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS", experience=4, consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        self.appointment = Appointment.objects.create(
            patient=self.patient, doctor=self.doctor,
            appointment_date=date.today() - timedelta(days=1),
            appointment_time=time(10, 0), reason_for_visit="Check-up",
            status=AppointmentStatus.COMPLETED,
        )

    def test_bill_id_and_total_amount_are_generated(self):
        bill = Billing.objects.create(
            appointment=self.appointment, patient=self.patient,
            amount=Decimal("500.00"), tax_amount=Decimal("90.00"),
            total_amount=Decimal("0.00"),
        )
        self.assertRegex(bill.bill_id, r"^BILL\d{6}$")
        self.assertEqual(bill.total_amount, Decimal("590.00"))
        self.assertEqual(bill.payment_status, PaymentStatus.PENDING)

    def test_payment_id_is_generated(self):
        bill = Billing.objects.create(
            appointment=self.appointment, patient=self.patient,
            amount=Decimal("500.00"), tax_amount=Decimal("0.00"),
            total_amount=Decimal("0.00"),
        )
        payment = Payment.objects.create(
            billing=bill, amount=Decimal("100.00"),
            payment_method=PaymentMethod.UPI, payment_type=PaymentType.ADVANCE,
            transaction_reference="TEST-UPI-001",
        )
        self.assertRegex(payment.payment_id, r"^PAY\d{6}$")

    def test_payment_form_rejects_zero_amount(self):
        form = PaymentForm(data={
            "amount": "0.00", "payment_method": PaymentMethod.CASH,
            "payment_type": PaymentType.ADVANCE, "transaction_reference": "",
        })
        self.assertFalse(form.is_valid())
        self.assertIn("amount", form.errors)

    def test_payment_form_accepts_positive_amount(self):
        form = PaymentForm(data={
            "amount": "100.00", "payment_method": PaymentMethod.UPI,
            "payment_type": PaymentType.ADVANCE, "transaction_reference": "UPI-001",
        })
        self.assertTrue(form.is_valid())

    def test_billing_form_rejects_negative_tax(self):
        form = BillingForm(data={"tax_type": "EXEMPT", "tax_amount": "-1.00"})
        self.assertFalse(form.is_valid())
        self.assertIn("tax_amount", form.errors)