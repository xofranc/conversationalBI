from django.db import models
from django.conf import settings


class QueryHistory(models.Model):

    class CharType(models.TextChoices):
        BAR = 'bar', 'Barras'
        LINE = 'line', 'Linea'
        PIE = 'pie', 'Torta'
        SCATTER = 'scatter', 'Dispersion'
        TABLE = 'table', 'Tabla'


    user = models.ForeignKey(settings.AUTH_USER_MODEL,
                             on_delete=models.CASCADE,
                             related_name='queries')

    dataset = models.ForeignKey('dataset.Dataset',
                                on_delete=models.CASCADE,
                                related_name='queries' )


    question = models.TextField()
    sql_generated = models.TextField(blank=True)
    execution_time = models.FloatField(default=0.0)
    success = models.BooleanField(default=False)
    error_msg = models.TextField(blank=True)


    #! Metricas para el trabajo de grado

    model_used = models.CharField(max_length=50,blank=True)
    retry_count = models.IntegerField(default=0)
    cached = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)


    class Meta:
        ordering = ['-created_at']

        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['dataset', 'success']),
            models.Index(fields=['user', 'success']),
        ]

    def __str__(self):
        return f"{self.user} / {self.question[:60]}"
