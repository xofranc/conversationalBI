# apps/core/views.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from .services.demo_service import DemoService


@api_view(['DELETE'])
@permission_classes([AllowAny])
def cleanup_session(request):
    """
    Limpia los datasets de una sesión de demo.
    DELETE /api/v1/core/session/
    """
    session_id = request.headers.get('X-Session-ID')
    if not session_id:
        return Response(
            {'error': 'X-Session-ID header required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        count = DemoService.cleanup_session(session_id)
        return Response(
            {'message': f'Se eliminaron {count} datasets'},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
