"""REST endpoints for demo-session cleanup."""

from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.core.application.dtos import DemoSessionInput


class CleanupSessionView(APIView):
    """Delete datasets associated with the supplied demo session."""

    permission_classes = [AllowAny]
    pagination_class = None
    use_cases = None

    def delete(self, request):
        session_id = request.headers.get("X-Session-ID")
        if not session_id:
            return Response(
                {"error": "X-Session-ID header required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            result = self.use_cases["cleanup_session"].execute(
                DemoSessionInput(session_id=session_id)
            )
            return Response(
                {"message": f"Se eliminaron {result.deleted_dataset_count} datasets"},
                status=status.HTTP_200_OK,
            )
        except Exception as error:
            return Response(
                {"error": str(error)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
