from django import forms

from .models import Billing, Payment


class BillingForm(forms.ModelForm):

    class Meta:
        model = Billing

        fields = [
            "tax_type",
            "tax_amount",
        ]

        widgets = {
            "tax_type": forms.Select(
                attrs={
                    "class": "form-select",
                }
            ),
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