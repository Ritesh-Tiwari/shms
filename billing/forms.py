from django import forms
from decimal import Decimal
from django.core.exceptions import ValidationError
from .models import Billing, Payment


class BillingForm(forms.ModelForm):

    class Meta:
        model = Billing

        fields = [
            "tax_type",
            "tax_amount",
        ]

        widgets = {
            
            "tax_amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0",
                }
            ),
        }

    def clean_tax_amount(self):
        tax_amount = self.cleaned_data.get("tax_amount")

        if tax_amount is None:
            return 0

        if tax_amount < 0:
            raise forms.ValidationError(
                "Tax amount cannot be negative."
            )

        return tax_amount


class PaymentForm(forms.ModelForm):

    class Meta:
        model = Payment

        fields = [
            "amount",
            "payment_method",
            "payment_type",
            "transaction_reference",
        ]

        widgets = {
            "amount": forms.NumberInput(
                attrs={
                    "class": "form-control",
                    "step": "0.01",
                    "min": "0.01",
                }
            ),
            "payment_method": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "payment_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
            "transaction_reference": forms.TextInput(
                attrs={
                    "class": "form-control",
                }
            ),
        }
        
    def clean_amount(self):
        amount = self.cleaned_data.get("amount")

        # Server-side positive amount validation
        if amount is None or amount <= Decimal("0"):
            raise ValidationError("Payment amount must be greater than zero.")

        return amount