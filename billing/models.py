from django.db import models

from appointments.models import Appointment
from patients.models import Patient


class PaymentStatus(models.TextChoices):
    PENDING = "PENDING", "Pending"
    PARTIAL = "PARTIAL", "Partial"
    PAID = "PAID", "Paid"


class PaymentMethod(models.TextChoices):
    CASH = "CASH", "Cash"
    CARD = "CARD", "Card"
    UPI = "UPI", "UPI"
    ONLINE = "ONLINE", "Online"


class PaymentType(models.TextChoices):
    ADVANCE = "ADVANCE", "Advance"
    PARTIAL = "PARTIAL", "Partial"
    FINAL = "FINAL", "Final"


class TaxType(models.TextChoices):
    EXEMPT = "EXEMPT", "Exempt"
    GST = "GST", "GST"
    OTHER = "OTHER", "Other"


class Billing(models.Model):

    bill_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    appointment = models.OneToOneField(
        Appointment,
        on_delete=models.CASCADE,
        related_name="billing",
    )

    patient = models.ForeignKey(
        Patient,
        on_delete=models.CASCADE,
        related_name="bills",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    tax_type = models.CharField(
        max_length=20,
        choices=TaxType.choices,
        default=TaxType.EXEMPT,
    )

    tax_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
    )

    total_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    bill_date = models.DateTimeField(
        auto_now_add=True,
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING,
    )

    class Meta:
        db_table = "billings"

        ordering = [
            "-bill_date",
        ]

        verbose_name = "Billing"
        verbose_name_plural = "Billings"

    def __str__(self):
        return self.bill_id

    def save(self, *args, **kwargs):

        if not self.bill_id:

            last_bill = (
                Billing.objects.order_by("-id").first()
            )

            if last_bill:

                last_id = int(
                    last_bill.bill_id.replace(
                        "BILL",
                        ""
                    )
                )

                self.bill_id = (
                    f"BILL{last_id + 1:06d}"
                )

            else:

                self.bill_id = "BILL000001"

        self.total_amount = (
            self.amount + self.tax_amount
        )

        super().save(*args, **kwargs)


class Payment(models.Model):

    payment_id = models.CharField(
        max_length=20,
        unique=True,
        blank=True,
    )

    billing = models.ForeignKey(
        Billing,
        on_delete=models.CASCADE,
        related_name="payments",
    )

    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
    )

    payment_method = models.CharField(
        max_length=20,
        choices=PaymentMethod.choices,
    )

    payment_type = models.CharField(
        max_length=20,
        choices=PaymentType.choices,
    )

    transaction_reference = models.CharField(
        max_length=100,
        blank=True,
    )

    payment_date = models.DateTimeField(
        auto_now_add=True,
    )

    class Meta:
        db_table = "payments"

        ordering = [
            "-payment_date",
        ]

        verbose_name = "Payment"
        verbose_name_plural = "Payments"

    def __str__(self):
        return self.payment_id

    def save(self, *args, **kwargs):

        if not self.payment_id:

            last_payment = (
                Payment.objects.order_by("-id").first()
            )

            if last_payment:

                last_id = int(
                    last_payment.payment_id.replace(
                        "PAY",
                        ""
                    )
                )

                self.payment_id = (
                    f"PAY{last_id + 1:06d}"
                )

            else:

                self.payment_id = "PAY000001"

        super().save(*args, **kwargs)