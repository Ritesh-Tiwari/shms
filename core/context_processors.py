from django.contrib.humanize.templatetags.humanize import naturaltime
from django.db.models import Count, F, Q, Window

from accounts.choices import UserRole
from core.models import Notification


MAX_RECENT_ACTIVITIES = 10


def recent_activities(request):
    if not request.user.is_authenticated:
        return {
            "notifications": [],
            "recent_activities": [],
            "recent_activity_ids": [],
            "unread_notification_count": 0,
        }

    notifications = list(
        Notification.objects.filter(
            recipient=request.user,
        ).annotate(
            unread_total=Window(
                expression=Count("pk", filter=Q(read_at__isnull=True)),
                partition_by=[F("recipient_id")],
            )
        ).order_by("-created_at", "-pk")[:MAX_RECENT_ACTIVITIES]
    )
    for notification in notifications:
        notification.time = naturaltime(notification.created_at)

    unread_count = notifications[0].unread_total if notifications else 0

    return {
        "notifications": notifications,
        "recent_activities": (
            notifications if request.user.role == UserRole.ADMIN else []
        ),
        "recent_activity_ids": [
            str(notification.pk) for notification in notifications
            if notification.read_at is None
        ],
        "unread_notification_count": unread_count,
    }
