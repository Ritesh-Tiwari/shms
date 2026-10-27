from .models import AuditLog


def log_security_event(
    request,
    *,
    action,
    outcome,
    target_user=None,
    target_identifier="",
    details=None,
):
    actor = None

    if (
        request is not None
        and request.user.is_authenticated
    ):
        actor = request.user

    ip_address = None
    user_agent = ""

    if request is not None:
        # Use the direct client address by default.
        # Only trust forwarded headers behind a configured,
        # trusted reverse proxy.
        ip_address = request.META.get("REMOTE_ADDR") or None
        user_agent = request.META.get(
            "HTTP_USER_AGENT", ""
        )[:500]

    return AuditLog.objects.create(
        actor=actor,
        action=action,
        outcome=outcome,
        target_user=target_user,
        target_identifier=(
            target_identifier
            or (
                target_user.email
                if target_user is not None
                else ""
            )
        ),
        ip_address=ip_address,
        user_agent=user_agent,
        details=details or {},
    )