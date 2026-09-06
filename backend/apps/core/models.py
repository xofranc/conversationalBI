# apps/core/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta


class DemoSession(models.Model):
    """Sesión anónima para modo demo."""
    
    session_id = models.CharField(max_length=36, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_active = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'demo_sessions'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"DemoSession({self.session_id[:8]}...)"
    
    @property
    def is_expired(self):
        """Sesión expira después de 24 horas de inactividad."""
        return timezone.now() - self.last_active > timedelta(hours=24)
    
    @classmethod
    def cleanup_expired(cls):
        """Elimina sesiones expiradas."""
        threshold = timezone.now() - timedelta(hours=24)
        return cls.objects.filter(last_active__lt=threshold).delete()
