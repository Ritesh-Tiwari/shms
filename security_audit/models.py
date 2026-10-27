from django.conf import settings
from django.db import models


class AuditLog(models.Model):

    class Outcome(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILURE = "FAILURE", "Failure"
        DENIED = "DENIED", "Denied"

    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_events",
    )

    action = models.CharField(max_length=64)

    # Preserve target details even if the account is deleted.
    target_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs_about",
    )

    target_identifier = models.CharField(
        max_length=254,
        blank=True,
    )

    outcome = models.CharField(
        max_length=10,
        choices=Outcome.choices,
    )

    timestamp = models.DateTimeField(auto_now_add=True)

    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
    )

    user_agent = models.CharField(
        max_length=500,
        blank=True,
    )

    details = models.JSONField(default=dict, blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["-timestamp"]),
            models.Index(fields=["action", "-timestamp"]),
            models.Index(fields=["outcome", "-timestamp"]),
        ]

    def __str__(self):
        return f"{self.action} - {self.outcome} - {self.timestamp}"