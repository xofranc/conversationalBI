from django.db import models


class ProjectPhase(models.Model):
    """Fases del roadmap del proyecto, editables desde el admin de Django."""

    class Status(models.TextChoices):
        COMPLETED = 'completed', 'Completada'
        IN_PROGRESS = 'in_progress', 'En progreso'
        PENDING = 'pending', 'Pendiente'
        BLOCKED = 'blocked', 'Bloqueada'

    order = models.PositiveIntegerField(default=0, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    date_completed = models.DateField(null=True, blank=True)
    github_url = models.URLField(blank=True)
    doc_url = models.URLField(blank=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'fase del proyecto'
        verbose_name_plural = 'fases del proyecto'

    def __str__(self):
        return f"{self.order}. {self.name} ({self.get_status_display()})"


class ProjectModule(models.Model):
    """Módulos/capacidades del copilot, editables desde el admin."""

    class Status(models.TextChoices):
        LIVE = 'live', 'En producción'
        BETA = 'beta', 'Beta'
        ALPHA = 'alpha', 'Alpha'
        PENDING = 'pending', 'Pendiente'

    order = models.PositiveIntegerField(default=0, db_index=True)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    icon = models.CharField(max_length=20, blank=True, help_text='Emoji o icono corto')

    class Meta:
        ordering = ['order']
        verbose_name = 'módulo'
        verbose_name_plural = 'módulos'

    def __str__(self):
        return f"{self.order}. {self.name} ({self.get_status_display()})"
