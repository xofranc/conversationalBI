from ..models import User
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth.password_validation import validate_password   
from django.contrib.auth import authenticate



class RegisterSerializer(serializers.ModelSerializer):
    
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    
    class Meta:
        model = User
        fields = ['email', 'first_name', 'last_name', 'password']
        extra_kwargs = {
            'password': {'write_only': True},
        }
        
    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name']
        )
        return user
    
    
    
class LoginSerializer(serializers.Serializer):

    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, data):
        
        user = authenticate(
            email=data['email'], 
            password=data['password']
            )
        
        if not user:
            raise serializers.ValidationError("Credenciales inválidas.")
        
        refresh = RefreshToken.for_user(user)
        
        return {
        "user": {
            "id": user.id,
            "email": user.email
        },
        "refresh": str(refresh),
        "access": str(refresh.access_token)
    }
    
    
class LogoutSerializer(serializers.Serializer):
    refresh = serializers.CharField()

    default_error_messages = {
        "bad_token": "Token inválido o expirado."
    }

    def validate_refresh(self, value):
        if not value.strip():
            raise serializers.ValidationError("Debe enviar el refresh token.")
        return value

    def save(self, **kwargs):
        try:
            token = RefreshToken(self.validated_data["refresh"])
            token.blacklist()
        except TokenError as e: #? Es mejor capturar la excepción específica de token inválido o expirado, que usar Exception, para evitar capturar errores no relacionados con el token.
            print(f"Error al invalidar el token: {str(e)}") #? Es útil imprimir el error para depuración, pero en producción se debería usar un sistema de logging adecuado.
            self.fail("bad_token")