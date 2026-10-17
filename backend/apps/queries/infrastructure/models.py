"""Django persistence models for query history and its related records."""

from django.conf import settings
from django.db import models


class QueryHistory(models.Model):
    class CharType(models.TextChoices):
        BAR = "bar", "Barras"
        LINE = "line", "Linea"
        PIE = "pie", "Torta"
        SCATTER = "scatter", "Dispersion"
        TABLE = "table", "Tabla"
        FORECAST = "forecast", "Pronostico"
        ANOMALY = "anomaly", "Anomalias"
        SEGMENT = "segment", "Segmentacion"
        DRIVERS = "drivers", "Factores"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="queries",
    )
    dataset = models.ForeignKey(
        "dataset.Dataset",
        on_delete=models.CASCADE,
        related_name="queries",
    )

    question = models.TextField()
    sql_generated = models.TextField(blank=True)
    execution_time = models.FloatField(default=0.0)
    success = models.BooleanField(default=False)
    error_msg = models.TextField(blank=True)

    #! Metricas para el trabajo de grado
    model_used = models.CharField(max_length=50, blank=True)
    retry_count = models.IntegerField(default=0)
    cached = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["dataset", "success"]),
            models.Index(fields=["user", "success"]),
        ]

    def __str__(self):
        return f"{self.user} / {self.question[:60]}"


class QueryResult(models.Model):
    query = models.OneToOneField(
        QueryHistory,
        on_delete=models.CASCADE,
        related_name="result",
    )

    result_json = models.JSONField(default=list)
    columns = models.JSONField(default=list)
    row_count = models.PositiveIntegerField(default=0)

    #! Respuesta en lenguaje natural (la conversación, no solo las filas)
    answer = models.TextField(blank=True)
    chart_type = models.CharField(
        max_length=10,
        choices=QueryHistory.CharType.choices,
        default=QueryHistory.CharType.TABLE,
    )

    chart_config = models.JSONField(default=dict)

    def __str__(self):
        return f"Resultado de la consulta {self.query_id}"


class QueryFeedback(models.Model):
    class Score(models.IntegerChoices):
        USEFUL = 1, "Útil"
        NOT_USEFUL = -1, "No útil"

    query = models.OneToOneField(
        QueryHistory,
        on_delete=models.CASCADE,
        related_name="feedback",
    )
    score = models.SmallIntegerField(choices=Score.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.score} → query {self.query_id}"


__all__ = ["QueryFeedback", "QueryHistory", "QueryResult"]
