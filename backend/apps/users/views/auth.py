
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle

from ..serializers.auth import RegisterSerializer, LoginSerializer, LogoutSerializer
from ..services import AuthService

'''
    se esta usando CreateAPIView para el registro porque es una vista genérica que maneja la creación de objetos, lo que se ajusta perfectamente a la funcionalidad de registrar un nuevo usuario. si se quiere anadir mas lógica personalizada, como enviar un correo de bienvenida o realizar alguna acción adicional después de crear el usuario, se puede sobrescribir el método post() para incluir esa lógica. o hacer uso de generics.GenericAPIView y definir el método post() completamente personalizado.
'''

#! Creamos una vista para registrar un nuevo usuario
class RegisterView(APIView):
    permission_classes = []
    throttle_classes = [AnonRateThrottle]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = AuthService.register(
            email      = serializer.validated_data['email'],
            password   = serializer.validated_data['password'],
            first_name = serializer.validated_data['first_name'],
            last_name  = serializer.validated_data['last_name'],
        )
        return Response({
            "id": user.id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
        }, status=status.HTTP_201_CREATED)
        
#! Creamos una vista para iniciar sesión y obtener un token JWT
class LoginView(APIView):
    permission_classes = []  # ← pública, no requiere auth
    throttle_classes = [AnonRateThrottle]  # ← limitamos la tasa para evitar abusos
   
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(serializer.validated_data, status=status.HTTP_200_OK)
    
    
class LogoutView(APIView):
    permission_classes = [IsAuthenticated]  # ← esta sí requiere auth
    throttle_classes = [UserRateThrottle]  # ← limitamos la tasa para evitar abusos

    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Sesión cerrada correctamente"},
            status=status.HTTP_200_OK
        ) 