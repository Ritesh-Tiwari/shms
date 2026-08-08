from django.contrib import messages
from django.shortcuts import redirect, render
from django.shortcuts import get_object_or_404
from django.db.models import Q
from django.core.paginator import Paginator

from accounts.forms import UserRegistrationForm
from .forms import DoctorForm
from .services import DoctorService
from .models import Doctor
from core.decorators import role_required
from accounts.choices import UserRole


@role_required(
    UserRole.ADMIN,
)
def register_doctor(request):

    if request.method == "POST":

        user_form = UserRegistrationForm(request.POST)

        doctor_form = DoctorForm(request.POST)

        if user_form.is_valid() and doctor_form.is_valid():

            DoctorService.create_doctor(

                user_data=user_form.cleaned_data,

                doctor_data=doctor_form.cleaned_data,

            )

            messages.success(
                request,
                "Doctor registered successfully.",
            )

            return redirect("doctors:list")
        
    else:

        user_form = UserRegistrationForm()

        doctor_form = DoctorForm()

    return render(
        request,
        "doctors/register.html",
        {
            "user_form": user_form,
            "doctor_form": doctor_form,
        },
    )

@role_required(
    UserRole.ADMIN,
)
def doctor_list(request):

    search = request.GET.get(
        "search",
        "",
    )

    doctors = Doctor.objects.select_related(
        "user",
    )

    if search:

        doctors = doctors.filter(

            Q(doctor_id__icontains=search)

            | Q(user__first_name__icontains=search)

            | Q(user__last_name__icontains=search)

            | Q(user__email__icontains=search)

            | Q(specialization__icontains=search)

        )
    paginator = Paginator(
        doctors,
        10,
    )

    page_number = request.GET.get(
        "page",
    )

    page_obj = paginator.get_page(
        page_number,
    )

    return render(
        request,
        "doctors/list.html",
        {
            "page_obj": page_obj,
            "search": search,
        },
    )

@role_required(
    UserRole.ADMIN,
)
def doctor_detail(request, pk):

    doctor = get_object_or_404(
        Doctor.objects.select_related("user"),
        pk=pk,
    )

    return render(
        request,
        "doctors/detail.html",
        {
            "doctor": doctor,
        },
    )

@role_required(
    UserRole.ADMIN,
)
def update_doctor(request, pk):

    doctor = get_object_or_404(
        Doctor,
        pk=pk,
    )

    if request.method == "POST":

        user_form = UserRegistrationForm(
            request.POST,
            instance=doctor.user,
        )

        doctor_form = DoctorForm(
            request.POST,
            instance=doctor,
        )

        if user_form.is_valid() and doctor_form.is_valid():

            DoctorService.update_doctor(
                doctor=doctor,
                user_data=user_form.cleaned_data,
                doctor_data=doctor_form.cleaned_data,
            )

            messages.success(
                request,
                "Doctor updated successfully.",
            )

            return redirect(
                "doctors:detail",
                doctor.pk,
            )

    else:

        user_form = UserRegistrationForm(
            instance=doctor.user,
        )

        doctor_form = DoctorForm(
            instance=doctor,
        )

    return render(
        request,
        "doctors/update.html",
        {
            "user_form": user_form,
            "doctor_form": doctor_form,
            "doctor": doctor,
        },
    )

@role_required(
    UserRole.ADMIN,
)
def delete_doctor(request, pk):

    doctor = get_object_or_404(
        Doctor,
        pk=pk,
    )

    if request.method == "POST":

        doctor.user.delete()

        messages.success(
            request,
            "Doctor deleted successfully.",
        )

        return redirect(
            "doctors:list",
        )

    return render(
        request,
        "doctors/delete.html",
        {
            "doctor": doctor,
        },
    )

