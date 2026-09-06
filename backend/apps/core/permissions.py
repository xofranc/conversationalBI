# apps/core/permissions.py
from rest_framework.permissions import BasePermission


class IsAuthenticatedOrDemo(BasePermission):
    """
    Permite acceso autenticado o anónimo en modo demo.
    En modo demo, usa X-Session-ID header para identificar sesiones.
    """
    
    def has_permission(self, request, view):
        # Si el usuario está autenticado, permitir
        if request.user and request.user.is_authenticated:
            return True
        
        # En modo demo, permitir con X-Session-ID
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            # Crear usuario anónimo temporal
            request.demo_session_id = session_id
            return True
        
        return False
    
    def has_object_permission(self, request, view, obj):
        # Si el usuario está autenticado, verificar propiedad
        if request.user and request.user.is_authenticated:
            return obj.user == request.user
        
        # En modo demo, verificar por session_id
        session_id = request.headers.get('X-Session-ID')
        if session_id and hasattr(obj, 'demo_session_id'):
            return obj.demo_session_id == session_id
        
        return False
