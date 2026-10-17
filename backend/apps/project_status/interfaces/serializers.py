"""DTO serializers for the public project roadmap response."""

from rest_framework import serializers


class ProjectPhaseSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    date_completed = serializers.DateField(allow_null=True)
    github_url = serializers.CharField(allow_blank=True)
    doc_url = serializers.CharField(allow_blank=True)


class ProjectModuleSerializer(serializers.Serializer):
    order = serializers.IntegerField()
    name = serializers.CharField()
    description = serializers.CharField(allow_blank=True)
    status = serializers.CharField()
    icon = serializers.CharField(allow_blank=True)
