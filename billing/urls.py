from django.urls import path

from . import views


app_name = "billing"


urlpatterns = [

    # -------------------------
    # Patient read-only access
    # -------------------------

    path(
        "my/",
        views.my_bills,
        name="my-bills",
    ),

    path(
        "my/<int:pk>/",
        views.my_bill_detail,
        name="my-bill-detail",
    ),

    path(
        "my/receipts/",
        views.my_payment_receipts,
        name="my-receipts",
    ),

    path(
        "my/receipts/<int:payment_id>/",
        views.my_payment_receipt,
        name="my-receipt",
    ),


    # -------------------------
    # Staff
    # -------------------------

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