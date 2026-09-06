# apps/core/services/demo_service.py
import logging
from django.db import transaction
from apps.dataset.models import Dataset
from apps.dataset.services import DatasetService
from apps.core.models import DemoSession

logger = logging.getLogger(__name__)


class DemoService:
    """Servicio para manejar sesiones anónimas y sus datasets."""
    
    @staticmethod
    def get_or_create_session(session_id: str) -> DemoSession:
        """Obtiene o crea una sesión de demo."""
        session, created = DemoSession.objects.get_or_create(
            session_id=session_id,
            defaults={'session_id': session_id}
        )
        logger.info('[DemoService] session_id=%s, created=%s', session_id, created)
        return session
    
    @staticmethod
    def get_demo_user(session_id: str):
        """
        Crea o obtiene un usuario temporal para la sesión de demo.
        Usa el session_id como identificador único.
        """
        from apps.users.models import User
        
        email = f"demo_{session_id}@demo.local"
        logger.info('[DemoService.get_demo_user] session_id=%s, email=%s', session_id, email)
        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'first_name': 'Demo',
                'last_name': 'User',
                'is_active': True,
            }
        )
        logger.info('[DemoService.get_demo_user] user_id=%s, created=%s', user.id, created)
        return user
    
    @staticmethod
    def get_session_datasets(session_id: str):
        """Obtiene los datasets de una sesión de demo."""
        user = DemoService.get_demo_user(session_id)
        return Dataset.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def cleanup_session(session_id: str):
        """Limpia todos los datasets de una sesión de demo."""
        user = DemoService.get_demo_user(session_id)
        datasets = Dataset.objects.filter(user=user)
        
        for dataset in datasets:
            try:
                DatasetService.delete(dataset.id, user)
            except Exception:
                # Si falla la eliminación, simplemente continuamos
                pass
        
        return datasets.count()
    
    @staticmethod
    def cleanup_all_expired():
        """Limpia todas las sesiones expiradas."""
        expired_sessions = DemoSession.objects.filter(
            last_active__lt=__import__('django.utils.timezone').now() - __import__('datetime').timedelta(hours=24)
        )
        
        total_cleaned = 0
        for session in expired_sessions:
            count = DemoService.cleanup_session(session.session_id)
            total_cleaned += count
            session.delete()
        
        return total_cleaned
