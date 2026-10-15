"""DRF serializers for HTTP payloads and application DTOs."""

from rest_framework import serializers


class DatasetUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000, default="", allow_blank=True)


class DatasetListSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    file_size = serializers.IntegerField()
    row_count = serializers.IntegerField()
    column_count = serializers.IntegerField()
    status = serializers.CharField()
    created_at = serializers.DateTimeField(allow_null=True)


class DatasetTableSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    table_name = serializers.CharField()
    row_count = serializers.IntegerField()
    column_count = serializers.IntegerField()
    columns_json = serializers.ListField(source="columns")


class DatasetDetailSerializer(serializers.Serializer):
    id = serializers.IntegerField(allow_null=True)
    owner = serializers.SerializerMethodField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    file_size = serializers.IntegerField()
    row_count = serializers.IntegerField()
    column_count = serializers.IntegerField()
    status = serializers.CharField()
    error_msg = serializers.CharField(source="error_message", allow_blank=True)
    schema_json = serializers.JSONField(source="schema")
    tables = DatasetTableSerializer(many=True, read_only=True)
    created_at = serializers.DateTimeField(allow_null=True)
    updated_at = serializers.DateTimeField(allow_null=True)

    def get_owner(self, _dataset):
        return self.context.get("owner", "")
