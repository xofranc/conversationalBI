from rest_framework.generics import CreateAPIView
from rest_framework.views import APIView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from ..models import User
from ..serializers.auth import RegisterSerializer, LoginSerializer, LogoutSerializer


'''
    se esta usando CreateAPIView para el registro porque es una vista genérica que maneja la creación de objetos, lo que se ajusta perfectamente a la funcionalidad de registrar un nuevo usuario. si se quiere anadir mas lógica personalizada, como enviar un correo de bienvenida o realizar alguna acción adicional después de crear el usuario, se puede sobrescribir el método post() para incluir esa lógica. o hacer uso de generics.GenericAPIView y definir el método post() completamente personalizado.
'''
#! Creamos una vista para registrar un nuevo usuario
class RegisterView(CreateAPIView):
    
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    
    
    #! Es posible que no necesitemos este método, pero lo dejamos por si queremos personalizar la respuesta
    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
#! Creamos una vista para iniciar sesión y obtener un token JWT
class LoginView(APIView):
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = self.serializer_class(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)

        return Response(
            serializer.validated_data,
            status=status.HTTP_200_OK
        )

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    def post(self, request):
        serializer = LogoutSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(
            {"message": "Sesión cerrada correctamente"},
            status=status.HTTP_200_OK)