from django.conf import settings
from django.db import models


class Notification(models.Model):
    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    actor_name = models.CharField(max_length=150, blank=True)
    message = models.CharField(max_length=255)
    target_url = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["-created_at", "-pk"]
        indexes = [
            models.Index(
                fields=["recipient", "read_at", "-created_at"],
                name="core_notif_recipient_read",
            ),
        ]

    def __str__(self):
        return f"Notification for {self.recipient_id}: {self.message}"
