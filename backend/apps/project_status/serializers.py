from rest_framework import serializers

from .models import ProjectModule, ProjectPhase


class ProjectPhaseSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectPhase
        fields = [
            "order",
            "name",
            "description",
            "status",
            "date_completed",
            "github_url",
            "doc_url",
        ]


class ProjectModuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProjectModule
        fields = ("order", "name", "description", "status", "icon")
