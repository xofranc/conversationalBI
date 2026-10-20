"""DRF serializers for HTTP payloads and application DTOs."""

from rest_framework import serializers


class QueryRequestSerializer(serializers.Serializer):
    question = serializers.CharField(
        min_length=5,
        max_length=500,
        error_messages={
            "min_length": "La pregunta debe tener al menos 5 caracteres.",
            "blank": "La pregunta no puede estar vacía.",
        },
    )
    dataset_id = serializers.IntegerField(min_value=1)


class QueryResponseSerializer(serializers.Serializer):
    query_id = serializers.IntegerField(allow_null=True)
    sql = serializers.CharField(allow_blank=True)
    success = serializers.BooleanField()
    error_msg = serializers.CharField(source="error_message", allow_blank=True)
    execution_time = serializers.FloatField()
    model_used = serializers.CharField(allow_blank=True)
    retry_count = serializers.IntegerField()
    cached = serializers.BooleanField()
    data = serializers.ListField()
    columns = serializers.ListField()
    chart_type = serializers.CharField()
    chart_config = serializers.JSONField()
    row_count = serializers.IntegerField()
    answer = serializers.CharField(allow_blank=True)
    suggestions = serializers.ListField(child=serializers.CharField(), required=False)

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # The established response only includes suggestions on failed queries.
        if representation["success"]:
            representation.pop("suggestions", None)
        return representation


class QueryResultSerializer(serializers.Serializer):
    result_json = serializers.ListField(source="data")
    columns = serializers.ListField()
    row_count = serializers.IntegerField()
    chart_type = serializers.CharField()
    chart_config = serializers.JSONField()
    answer = serializers.CharField(allow_blank=True)


class QueryHistorySerializer(serializers.Serializer):
    id = serializers.IntegerField(source="query_id", allow_null=True)
    question = serializers.CharField()
    sql_generated = serializers.CharField(source="sql", allow_blank=True)
    execution_time = serializers.FloatField()
    success = serializers.BooleanField()
    error_msg = serializers.CharField(source="error_message", allow_blank=True)
    model_used = serializers.CharField(allow_blank=True)
    retry_count = serializers.IntegerField()
    cached = serializers.BooleanField()
    created_at = serializers.DateTimeField(allow_null=True)
    result = QueryResultSerializer(allow_null=True)


class QueryHistoryListSerializer(serializers.Serializer):
    id = serializers.IntegerField(source="query_id", allow_null=True)
    question = serializers.CharField()
    success = serializers.BooleanField()
    execution_time = serializers.FloatField()
    model_used = serializers.CharField(allow_blank=True)
    retry_count = serializers.IntegerField()
    cached = serializers.BooleanField()
    created_at = serializers.DateTimeField(allow_null=True)


class FeedbackSerializer(serializers.Serializer):
    score = serializers.IntegerField()
    comment = serializers.CharField(required=False, allow_blank=True, default="")
