from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect, render
from django.views.decorators.http import require_POST

from security_audit.models import AuditLog
from security_audit.services import log_security_event


def login_view(request):

    if request.user.is_authenticated:
        return redirect("dashboard:dashboard")

    if request.method == "POST":

        username = request.POST.get("username")
        password = request.POST.get("password")

        user = authenticate(
            request,
            username=username,
            password=password,
        )

        if user:

            login(
                request,
                user,
            )
            log_security_event(
                request,
                action="LOGIN",
                outcome=AuditLog.Outcome.SUCCESS,
                target_user=user,
            )

            messages.success(
                request,
                "Login successful.",
            )

            return redirect("dashboard:dashboard")

        log_security_event(
            request,
            action="LOGIN_FAILURE",
            outcome=AuditLog.Outcome.FAILURE,
            target_identifier=request.POST.get("username", ""),
        )

        messages.error(
            request,
            "Invalid username or password.",
        )

    return render(
        request,
        "accounts/login.html",
    )

@require_POST
def logout_view(request):

    if request.user.is_authenticated:
        log_security_event(
            request,
            action="LOGOUT",
            outcome=AuditLog.Outcome.SUCCESS,
            target_user=request.user,
        )

    logout(request)

    messages.success(
        request,
        "Logged out successfully.",
    )

    return redirect("accounts:login")