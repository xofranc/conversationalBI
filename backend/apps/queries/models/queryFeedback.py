from django.db import models
from .queryHistory import QueryHistory

class QueryFeedback(models.Model):

    class Score(models.IntegerChoices):
        USEFUL = 1, 'Útil'
        NOT_USEFUL = -1, 'No útil'

    query = models.OneToOneField(
        QueryHistory,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    score = models.SmallIntegerField(choices=Score.choices)
    comment = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback {self.score} → query {self.query_id}"