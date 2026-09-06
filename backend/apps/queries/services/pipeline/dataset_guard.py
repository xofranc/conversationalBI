# apps/queries/services/pipeline/dataset_guard.py
import os
import logging

from django.conf import settings
from rest_framework.exceptions import NotFound, ValidationError

from apps.dataset.models import Dataset
from apps.dataset.repositories import DatasetRepository
from apps.dataset.services.database_service import DatabaseService

from .base import Middleware

logger = logging.getLogger(__name__)


class DatasetGuard(Middleware):
    """Validates dataset existence and status, materializes if needed."""
    
    def process(self, context: dict) -> dict:
        dataset_id = context['dataset_id']
        logger.info('[DatasetGuard] dataset_id=%s', dataset_id)
        
        # Validate dataset exists
        try:
            dataset = DatasetRepository.get_by_id(dataset_id)
        except Dataset.DoesNotExist:
            logger.warning('[DatasetGuard] Dataset %s no encontrado', dataset_id)
            raise NotFound('Dataset no encontrado.')
        
        # Validate dataset is ready
        if dataset.status != Dataset.Status.READY:
            logger.warning('[DatasetGuard] Dataset %s no está listo (status=%s)', dataset_id, dataset.status)
            raise ValidationError(
                {'dataset_id': f'El dataset no está listo para consultas (estado: {dataset.status}).'}
            )
        
        # Materialize if needed (lazy materialization)
        if not DatabaseService.exists(dataset.db_path):
            abs_file = os.path.join(settings.MEDIA_ROOT, dataset.file_path)
            logger.info('[DatasetGuard] Materializando dataset %s...', dataset_id)
            dataset.db_path = DatabaseService.materialize(dataset.id, abs_file)
            dataset.save(update_fields=['db_path', 'updated_at'])
        
        # Add dataset to context
        context['dataset'] = dataset
        context['version'] = dataset.updated_at.isoformat()
        
        logger.info('[DatasetGuard] OK db_path=%s', dataset.db_path)
        return context
