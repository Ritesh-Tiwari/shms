from django.conf import settings
from django.db import models
from django.utils import timezone


class Receptionist(models.Model):

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="receptionist_profile",
    )

    receptionist_id = models.CharField(
        max_length=20,
        unique=True,
        null=True,
        blank=True,
        editable=False,
    )

    joining_date = models.DateField(
        default=timezone.localdate,
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
    )

    updated_at = models.DateTimeField(
        auto_now=True,
    )

    class Meta:

        db_table = "receptionists"

        ordering = [
            "receptionist_id",
        ]

        verbose_name = "Receptionist"

        verbose_name_plural = "Receptionists"

    def __str__(self):

        return (
            f"{self.receptionist_id} - "
            f"{self.user.get_full_name()}"
        )

    def save(self, *args, **kwargs):

        if not self.receptionist_id:

            # First save creates the database primary key.
            if not self.pk:
                super().save(*args, **kwargs)

            # Generate a stable business identifier.
            self.receptionist_id = (
                f"REC{self.pk:06d}"
            )

            update_fields = kwargs.get(
                "update_fields"
            )

            if update_fields is not None:
                kwargs["update_fields"] = (
                    set(update_fields)
                    | {"receptionist_id"}
                )

        super().save(*args, **kwargs)