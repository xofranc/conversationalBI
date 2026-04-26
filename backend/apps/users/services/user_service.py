# apps/users/services/user_service.py
from django.db.models import F
from ..models import User, Profile


class UserService:

    # ── Cuota ─────────────────────────────────────────────────────────────
    @staticmethod
    def can_query(user: User) -> bool:
        """
        Verifica si el usuario tiene cuota disponible antes de invocar el LLM.
        Llamado por QueryService como primer guard.
        """
        try:
            profile = user.profile
        except Profile.DoesNotExist:
            return False

        if not hasattr(profile, 'query_count') or not hasattr(profile, 'query_limit'):
            # Profile no tiene campos de cuota todavía — permitir por defecto
            return True

        return profile.query_count < profile.query_limit

    @staticmethod
    def increment_usage(user: User) -> None:
        """
        Incrementa el contador de consultas del usuario.
        Usa F() para evitar race conditions con requests concurrentes.
        """
        try:
            Profile.objects.filter(user=user).update(
                query_count=F('query_count') + 1
            )
        except Exception:
            # Si Profile no tiene query_count, no bloqueamos el flujo
            pass

    # ── Permisos sobre datasets ────────────────────────────────────────────
    @staticmethod
    def can_access_dataset(user: User, dataset_id: int) -> bool:
        """
        Verifica si el usuario es propietario del dataset.
        Llamado por QueryViewSet antes de ejecutar cualquier consulta.
        """
        from ...dataset.models import Dataset
        return Dataset.objects.filter(
            id   = dataset_id,
            user = user
        ).exists()