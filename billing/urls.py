from django.urls import path

from . import views


app_name = "billing"


urlpatterns = [

    path(
        "create/<int:appointment_id>/",
        views.create_bill,
        name="create",
    ),

    path(
        "<int:pk>/",
        views.billing_detail,
        name="detail",
    ),

    path(
        "<int:billing_id>/payment/create/",
        views.create_payment,
        name="payment_create",
    ),

    path(
        "payment/<int:payment_id>/receipt/",
        views.payment_receipt,
        name="payment_receipt",
    ),
    path(
        "payment/<int:payment_id>/receipt/pdf/",
        views.payment_receipt_pdf,
        name="payment_receipt_pdf",
    ),
]