from functools import wraps

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.contrib import messages
from django.shortcuts import redirect

def role_required(*allowed_roles):

    def decorator(view_func):

        @login_required
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):

            if request.user.role not in allowed_roles:

                messages.error(
                    request,
                    "You do not have permission to access this page.",
                )

            return view_func(
                request,
                *args,
                **kwargs,
            )

        return wrapper

    return decorator