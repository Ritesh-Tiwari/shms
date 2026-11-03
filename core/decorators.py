from functools import wraps
from django.core.exceptions import PermissionDenied
# from django.contrib import messages
from django.contrib.auth.decorators import login_required
# from django.shortcuts import redirect
from security_audit.models import AuditLog
from security_audit.services import log_security_event


def role_required(*allowed_roles):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if request.user.role not in allowed_roles:
                log_security_event(
                    request,
                    action="ACCESS_DENIED",
                    outcome=AuditLog.Outcome.DENIED,
                    details={"view": view_func.__name__},
                )
                raise PermissionDenied

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator