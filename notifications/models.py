from django.db import models

class Notification(models.Model):
    """
    Represents a notification in the system (e.g., when an investor follows a startup
    or when a message is received).
    """
    class Type(models.TextChoices):
        FOLLOW = "follow", "Follow"
        MESSAGE = "message", "Message"

    investor = models.ForeignKey(
        "investors.Investor",
        on_delete=models.SET_NULL,
        null=True, blank=True,
        db_column="investor_id",
        related_name="notifications",
    )
    startup = models.ForeignKey(
        "startups.Startup",
        on_delete=models.CASCADE,
        null=True, blank=True,
        db_column="startup_id",
        related_name="notifications",
    )

    type = models.CharField(max_length=20, choices=Type.choices)
    title = models.CharField(max_length=200)
    body = models.TextField(blank=True, default="")
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "notifications_notification"   # важливо, залиш як було
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.type}] startup={getattr(self.startup, 'id', None)} investor={getattr(self.investor, 'id', None)}"
