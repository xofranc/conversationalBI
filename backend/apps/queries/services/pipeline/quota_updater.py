# apps/queries/services/pipeline/quota_updater.py
from .base import Middleware
from apps.users.services import UserService


class QuotaUpdater(Middleware):
    """Updates user quota after query execution."""
    
    def process(self, context: dict) -> dict:
        user = context['user']
        UserService.increment_usage(user)
        return context
