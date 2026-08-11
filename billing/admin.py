from django.contrib import admin

from .models import Billing, Payment


@admin.register(Billing)
class BillingAdmin(admin.ModelAdmin):

    list_display = (
        "bill_id",
        "patient",
        "appointment",
        "amount",
        "tax_type",
        "tax_amount",
        "total_amount",
        "payment_status",
        "bill_date",
    )

    list_filter = (
        "payment_status",
        "tax_type",
    )

    search_fields = (
        "bill_id",
        "patient__patient_id",
        "appointment__appointment_id",
    )


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):

    list_display = (
        "payment_id",
        "billing",
        "amount",
        "payment_method",
        "payment_type",
        "transaction_reference",
        "payment_date",
    )

    list_filter = (
        "payment_method",
        "payment_type",
    )

    search_fields = (
        "payment_id",
        "billing__bill_id",
        "transaction_reference",
    )