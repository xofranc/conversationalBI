"""Django persistence model for demo sessions."""

from django.db import models


class DemoSession(models.Model):
    """Sesión anónima para modo demo."""

    session_id = models.CharField(max_length=36, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "demo_sessions"
        ordering = ["-created_at"]

    def __str__(self):
        return f"DemoSession({self.session_id[:8]}...)"

__all__ = ["DemoSession"]
