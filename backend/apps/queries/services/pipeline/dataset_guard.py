# apps/queries/services/pipeline/dataset_guard.py
import os

from django.conf import settings
from rest_framework.exceptions import NotFound, ValidationError

from apps.dataset.models import Dataset
from apps.dataset.repositories import DatasetRepository
from apps.dataset.services.database_service import DatabaseService

from .base import Middleware


class DatasetGuard(Middleware):
    """Validates dataset existence and status, materializes if needed."""
    
    def process(self, context: dict) -> dict:
        dataset_id = context['dataset_id']
        
        # Validate dataset exists
        try:
            dataset = DatasetRepository.get_by_id(dataset_id)
        except Dataset.DoesNotExist:
            raise NotFound('Dataset no encontrado.')
        
        # Validate dataset is ready
        if dataset.status != Dataset.Status.READY:
            raise ValidationError(
                {'dataset_id': f'El dataset no está listo para consultas (estado: {dataset.status}).'}
            )
        
        # Materialize if needed (lazy materialization)
        if not DatabaseService.exists(dataset.db_path):
            abs_file = os.path.join(settings.MEDIA_ROOT, dataset.file_path)
            dataset.db_path = DatabaseService.materialize(dataset.id, abs_file)
            dataset.save(update_fields=['db_path', 'updated_at'])
        
        # Add dataset to context
        context['dataset'] = dataset
        context['version'] = dataset.updated_at.isoformat()
        
        return context
