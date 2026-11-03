from datetime import date, time, timedelta
from decimal import Decimal
from django.test import TestCase
from django.urls import reverse
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


class BillingPdfAccessTests(TestCase):
    def setUp(self):
        self.patient_user = User.objects.create_user(
            username="invoice-patient",
            email="invoice-patient@example.com",
            password="test-password-123",
            role=UserRole.PATIENT,
            first_name="Invoice",
            last_name="Patient",
        )
        patient = Patient.objects.create(
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
        self.doctor_user = User.objects.create_user(
            username="invoice-doctor",
            email="invoice-doctor@example.com",
            password="test-password-123",
            role=UserRole.DOCTOR,
            first_name="Invoice",
            last_name="Doctor",
        )
        doctor = Doctor.objects.create(
            user=self.doctor_user,
            specialization=SpecializationChoices.GENERAL_PHYSICIAN,
            qualification="MBBS",
            experience=4,
            consultation_fee=Decimal("500.00"),
            address="Clinic Road",
        )
        appointment = Appointment.objects.create(
            patient=patient,
            doctor=doctor,
            appointment_date=date.today(),
            appointment_time=time(10, 0),
            reason_for_visit="Check-up",
            status=AppointmentStatus.COMPLETED,
        )
        self.billing = Billing.objects.create(
            appointment=appointment,
            patient=patient,
            amount=Decimal("500.00"),
            tax_amount=Decimal("90.00"),
            total_amount=Decimal("590.00"),
        )
        self.payment = Payment.objects.create(
            billing=self.billing,
            amount=Decimal("100.00"),
            payment_method=PaymentMethod.UPI,
            payment_type=PaymentType.ADVANCE,
            transaction_reference="TEST-UPI-001",
        )
        self.admin = User.objects.create_user(
            username="invoice-admin",
            email="invoice-admin@example.com",
            password="TestPassword123!",
            role=UserRole.ADMIN,
        )
        self.unassigned_doctor = User.objects.create_user(
            username="unassigned-doctor",
            email="unassigned-doctor@example.com",
            password="TestPassword123!",
            role=UserRole.DOCTOR,
        )
        self.receptionist = User.objects.create_user(
            username="invoice-receptionist",
            email="invoice-receptionist@example.com",
            password="test-password-123",
            role=UserRole.RECEPTIONIST,
        )

    def test_receptionist_can_view_and_download_invoice_pdf(self):
        self.client.force_login(self.receptionist)

        detail_response = self.client.get(
            reverse("billing:detail", args=[self.billing.pk])
        )
        self.assertEqual(detail_response.status_code, 200)
        self.assertContains(detail_response, "Download Invoice PDF")

        pdf_response = self.client.get(
            reverse("billing:pdf", args=[self.billing.pk])
        )
        self.assertEqual(pdf_response.status_code, 200)
        self.assertEqual(pdf_response["Content-Type"], "application/pdf")
        self.assertIn(
            f'invoice_{self.billing.bill_id}.pdf',
            pdf_response["Content-Disposition"],
        )
        self.assertTrue(pdf_response.content.startswith(b"%PDF"))

    def test_bill_detail_actions_match_staff_permissions(self):
        detail_url = reverse("billing:detail", args=[self.billing.pk])
        payment_url = reverse(
            "billing:payment_create",
            args=[self.billing.pk],
        )
        receipt_url = reverse(
            "billing:payment_receipt",
            args=[self.payment.pk],
        )
        receipt_pdf_url = reverse(
            "billing:payment_receipt_pdf",
            args=[self.payment.pk],
        )

        for user in (self.admin, self.doctor_user, self.receptionist):
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(detail_url)
                self.assertEqual(response.status_code, 200)
                self.assertContains(response, 'onclick="window.print()"')
                self.assertEqual(
                    self.client.get(
                        reverse(
                            "appointments:detail",
                            args=[self.billing.appointment.pk],
                        )
                    ).status_code,
                    200,
                )
                self.assertEqual(
                    self.client.get(
                        reverse("billing:pdf", args=[self.billing.pk])
                    ).status_code,
                    200,
                )

        for user in (self.admin, self.doctor_user):
            with self.subTest(role=user.role, action="payment"):
                self.client.force_login(user)
                response = self.client.get(detail_url)
                self.assertContains(response, payment_url)
                self.assertContains(response, receipt_url)
                self.assertEqual(
                    self.client.get(payment_url).status_code,
                    200,
                )
                self.assertEqual(
                    self.client.get(receipt_url).status_code,
                    200,
                )

        self.client.force_login(self.receptionist)
        response = self.client.get(detail_url)
        self.assertNotContains(response, payment_url)
        self.assertContains(response, receipt_pdf_url)
        self.assertContains(response, "Download Receipt")
        self.assertNotContains(response, "Collect Payment")
        self.assertNotContains(response, "Add Payment")
        self.assertEqual(self.client.get(payment_url).status_code, 403)
        self.assertEqual(self.client.get(receipt_url).status_code, 403)
        self.assertEqual(
            self.client.get(receipt_pdf_url).status_code,
            200,
        )

    def test_patient_has_only_patient_billing_routes(self):
        self.client.force_login(self.patient_user)

        self.assertEqual(
            self.client.get(
                reverse("billing:detail", args=[self.billing.pk])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse("billing:my-bill-detail", args=[self.billing.pk])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("billing:pdf", args=[self.billing.pk])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("billing:my-receipt", args=[self.payment.pk])
            ).status_code,
            200,
        )
        self.assertEqual(
            self.client.get(
                reverse("billing:payment_create", args=[self.billing.pk])
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "billing:payment_receipt",
                    args=[self.payment.pk],
                )
            ).status_code,
            403,
        )
        self.assertEqual(
            self.client.get(
                reverse(
                    "billing:payment_receipt_pdf",
                    args=[self.payment.pk],
                )
            ).status_code,
            200,
        )

    def test_unassigned_doctor_cannot_access_another_doctors_bill(self):
        self.client.force_login(self.unassigned_doctor)

        for route_name, object_id in (
            ("billing:detail", self.billing.pk),
            ("billing:pdf", self.billing.pk),
            ("billing:payment_receipt", self.payment.pk),
            ("billing:payment_receipt_pdf", self.payment.pk),
        ):
            with self.subTest(route=route_name):
                self.assertEqual(
                    self.client.get(
                        reverse(route_name, args=[object_id])
                    ).status_code,
                    404,
                )

        response = self.client.get(
            reverse("billing:payment_create", args=[self.billing.pk])
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(
            self.client.get(response.url).status_code,
            404,
        )

    def test_receipt_pdf_is_generated_for_authorized_users_and_scoped(self):
        receipt_pdf_url = reverse(
            "billing:payment_receipt_pdf",
            args=[self.payment.pk],
        )

        for user in (
            self.admin,
            self.doctor_user,
            self.receptionist,
            self.patient_user,
        ):
            with self.subTest(role=user.role):
                self.client.force_login(user)
                response = self.client.get(receipt_pdf_url)
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response["Content-Type"], "application/pdf")
                self.assertIn(
                    f'receipt_{self.payment.payment_id}.pdf',
                    response["Content-Disposition"],
                )
                self.assertTrue(response.content.startswith(b"%PDF"))

        other_patient = User.objects.create_user(
            username="other-invoice-patient",
            email="other-invoice-patient@example.com",
            password="testpass123",
            role=UserRole.PATIENT,
        )
        self.client.force_login(other_patient)
        self.assertEqual(
            self.client.get(receipt_pdf_url).status_code,
            404,
        )