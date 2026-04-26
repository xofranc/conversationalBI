from rest_framework import serializers
from ..models import QueryHistory, QueryResult, QueryFeedback


class QueryResultSerializer(serializers.ModelSerializer):
    class Meta:
        model  = QueryResult
        fields = ['result_json', 'columns', 'row_count', 'chart_type', 'chart_config']


class QueryHistorySerializer(serializers.ModelSerializer):
    result = QueryResultSerializer(read_only=True)

    class Meta:
        model  = QueryHistory
        fields = [
            'id', 'question', 'sql_generated', 'execution_time',
            'success', 'error_msg', 'model_used', 'retry_count',
            'cached', 'created_at', 'result',
        ]


class FeedbackSerializer(serializers.Serializer):
    score   = serializers.ChoiceField(choices=[1, -1])
    comment = serializers.CharField(required=False, allow_blank=True, default='')