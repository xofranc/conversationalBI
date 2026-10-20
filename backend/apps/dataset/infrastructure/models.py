"""Django persistence models for datasets."""

from django.conf import settings
from django.db import models


class Dataset(models.Model):
    class Status(models.TextChoices):
        READY = "ready", "Ready"
        INACTIVE = "inactive", "Inactive"
        ERROR = "error", "Error"
        PROCESSING = "processing", "Processing"
        UPLOADED = "uploaded", "Uploaded"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="datasets",
    )

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    #! RUta de acceso al archivo subido
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0)

    #! Base de datos SQLite materializada (relativa a MEDIA_ROOT).
    #! Las consultas se ejecutan contra ella, no contra el archivo original.
    db_path = models.CharField(max_length=500, blank=True)

    #! contrato con el dataset, con ai engine
    schema_json = models.JSONField(default=dict)

    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)

    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING,
    )

    error_msg = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["user", "status"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.status})"

class DatasetTable(models.Model):
    """Una hoja de Excel o tabla dentro de un dataset."""

    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name="tables",
    )

    table_name = models.CharField(max_length=255)
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    columns_json = models.JSONField(default=list)

    class Meta:
        unique_together = ("dataset", "table_name")
        ordering = ["table_name"]

    def __str__(self):
        return f"{self.dataset.name} / {self.table_name}"


__all__ = ["Dataset", "DatasetTable"]
