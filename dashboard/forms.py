from django import forms


REPORT_CHOICES = (
    ("patients", "Patient Registration Report"),
    ("appointments", "Appointment Summary Report"),
    ("doctor_schedules", "Doctor Schedule Report"),
    ("prescriptions", "Prescription Report"),
    ("billing_revenue", "Billing & Revenue Report"),
    ("payment_status", "Payment Status Report"),
)


class ReportFilterForm(forms.Form):
    report = forms.ChoiceField(
        choices=REPORT_CHOICES,
        widget=forms.Select(
            attrs={
                "class": (
                    "w-full rounded-lg bg-surface-container-low px-md py-sm "
                    "font-body-sm text-body-sm text-on-surface"
                )
            }
        ),
    )
    start_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": (
                    "w-full rounded-lg bg-surface-container-low px-md py-sm "
                    "font-body-sm text-body-sm text-on-surface"
                ),
            }
        ),
    )
    end_date = forms.DateField(
        required=False,
        input_formats=["%Y-%m-%d"],
        widget=forms.DateInput(
            attrs={
                "type": "date",
                "class": (
                    "w-full rounded-lg bg-surface-container-low px-md py-sm "
                    "font-body-sm text-body-sm text-on-surface"
                ),
            }
        ),
    )

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get("start_date")
        end_date = cleaned_data.get("end_date")

        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(
                "The start date must be on or before the end date."
            )

        return cleaned_data
