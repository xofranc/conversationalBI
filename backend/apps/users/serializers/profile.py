from ..models import Profile
from rest_framework import serializers

class ProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = Profile
        fields = ['bio', 'phone_number', 'birth_date']
        
        def validate_phone_number(self, value):
            if value and not value.isdigit():
                raise serializers.ValidationError("El número de teléfono debe contener solo dígitos.")
            if value and len(value) != 10:
                raise serializers.ValidationError("El número de teléfono debe tener exactamente 10 dígitos.")
            return value