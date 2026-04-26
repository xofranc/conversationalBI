from django.db import models
from .queryHistory import QueryHistory

class QueryResult(models.Model):

    query = models.OneToOneField(
        QueryHistory,
        on_delete=models.CASCADE,
        related_name='result'
    )


    result_json = models.JSONField(default=list)
    columns = models.JSONField(default=list)
    row_count = models.PositiveIntegerField(default=0)
    chart_type = models.CharField(max_length=10,
                                 choices=QueryHistory.CharType.choices,
                                 default=QueryHistory.CharType.TABLE
                                 )

    chart_config = models.JSONField(default=dict)

    def __str__(self):
        return f"Resultado de la consulta {self.query_id}"