from django.shortcuts import render

# Create your views here.

def dashboard(request):

    context = {

        "total_patients": 0,
        "total_doctors": 0,
        "total_appointments": 0,
        "total_revenue": 0,

    }

    return render(
        request,
        "dashboard/dashboard.html",
        context,
    )