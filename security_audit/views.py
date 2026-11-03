from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import render

from accounts.choices import UserRole
from core.decorators import role_required

from .models import AuditLog


@role_required(UserRole.ADMIN)
def audit_log_list(request):
    query = request.GET.get("q", "").strip()
    selected_action = request.GET.get("action", "").strip()
    selected_outcome = request.GET.get("outcome", "").strip()

    events = AuditLog.objects.select_related("actor", "target_user")

    if query:
        events = events.filter(
            Q(actor__email__icontains=query)
            | Q(target_identifier__icontains=query)
            | Q(action__icontains=query)
        )

    actions = AuditLog.objects.order_by().values_list(
        "action", flat=True
    ).distinct()
    if selected_action in actions:
        events = events.filter(action=selected_action)
    else:
        selected_action = ""

    valid_outcomes = {value for value, _ in AuditLog.Outcome.choices}
    if selected_outcome in valid_outcomes:
        events = events.filter(outcome=selected_outcome)
    else:
        selected_outcome = ""

    page_obj = Paginator(events, 25).get_page(request.GET.get("page"))

    return render(
        request,
        "security_audit/log_list.html",
        {
            "page_obj": page_obj,
            "query": query,
            "selected_action": selected_action,
            "selected_outcome": selected_outcome,
            "action_choices": actions,
            "outcome_choices": AuditLog.Outcome.choices,
        },
    )
