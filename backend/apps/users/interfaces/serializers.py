"""DRF serializers for the profile HTTP contract and application DTOs."""

from rest_framework import serializers


class ProfileSerializer(serializers.Serializer):
    bio = serializers.CharField(required=False, allow_blank=True)
    phone_number = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    birth_date = serializers.DateField(required=False, allow_null=True)
