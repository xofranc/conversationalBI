"""REST adapter for profile use cases; no ORM access is performed here."""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.users.application.dtos import GetProfileInput, UpdateProfileInput

from .serializers import ProfileSerializer


class ProfileView(APIView):
    permission_classes = [IsAuthenticated]
    pagination_class = None
    use_cases = None

    def get(self, request):
        dto = self.use_cases["get_profile"].execute(
            GetProfileInput(user_id=request.user.pk)
        )
        return Response(ProfileSerializer(dto).data)

    def patch(self, request):
        serializer = ProfileSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        try:
            dto = self.use_cases["update_profile"].execute(UpdateProfileInput(
                user_id=request.user.pk,
                bio=values.get("bio"),
                phone_number=values.get("phone_number"),
                birth_date=values.get("birth_date"),
                update_bio="bio" in values,
                update_phone_number="phone_number" in values,
                update_birth_date="birth_date" in values,
            ))
        except ValueError as error:
            message = str(error)
            if message == "El número de teléfono debe contener solo dígitos":
                message += "."
            elif message == "El número de teléfono debe tener exactamente 10 dígitos":
                message += "."
            return Response(
                {"phone_number": [message]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(ProfileSerializer(dto).data)
