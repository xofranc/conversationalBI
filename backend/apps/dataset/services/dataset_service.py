import os
import logging
from django.conf import settings

from apps.dataset.repositories import DatasetRepository
from ..models import Dataset
from .database_service import DatabaseService
from .file_service import FileService
from .schema_service import SchemaService

logger = logging.getLogger(__name__)


class DatasetService:
    
    """
        Orquesta, Solo coordina, no tiene logica de archivos 
        ni de pandas directamente
    """
    
    @staticmethod
    def create(file, user, name: str, description: str = "") -> Dataset:
        logger.info('[DatasetService.create] Inicio: file=%s, user_id=%s, name=%s', file.name, user.id, name)
        FileService.validate(file)
        logger.info('[DatasetService.create] Validación OK')
        
        dataset = DatasetRepository.create_dataset(
            user=user,
            name=name,
            description=description,
            file_size=file.size
        )
        logger.info('[DatasetService.create] Dataset creado en DB: id=%s', dataset.id)
        
        try:
            dataset.status = Dataset.Status.PROCESSING
            dataset.file_path = FileService.save(file, user.id)
            dataset.save(update_fields=["status", "file_path", "updated_at"])
            logger.info('[DatasetService.create] Archivo guardado: %s', dataset.file_path)

            abs_path = os.path.join(settings.MEDIA_ROOT, dataset.file_path)
            logger.info('[DatasetService.create] MEDIA_ROOT=%s, abs_path=%s', settings.MEDIA_ROOT, abs_path)

            # Materializa el schema Postgres del dataset: las consultas y
            # los análisis se ejecutan contra él, sin releer el archivo.
            logger.info('[DatasetService.create] Iniciando materialize...')
            dataset.db_path = DatabaseService.materialize(dataset.id, abs_path)
            dataset.save(update_fields=["db_path", "updated_at"])
            logger.info('[DatasetService.create] Materialize OK: db_path=%s', dataset.db_path)

            schema = SchemaService.extract(abs_path)
            row_count = sum(t["row_count"] for t in schema["tables"])
            col_count = sum(len(t["columns"]) for t in schema["tables"])
            logger.info('[DatasetService.create] Schema extraído: tables=%s, rows=%s, cols=%s', len(schema["tables"]), row_count, col_count)

            for tabla_data in schema["tables"]:
                DatasetRepository.create_table(dataset, tabla_data)

            dataset.mark_ready(schema, row_count, col_count) 
            logger.info('[DatasetService.create] Dataset mark_ready: id=%s', dataset.id)
            
        except Exception as exc:
            logger.error('[DatasetService.create] Error en paso intermedio: %s', exc, exc_info=True)
            dataset.mark_error(str(exc))
            raise
        
        return dataset
    
    @staticmethod
    def delete(dataset_id: int, user) -> None:
        dataset = DatasetRepository.get_by_id(dataset_id)
        if dataset.user != user:
            raise PermissionError("No tienes permiso para eliminar este dataset.")
        
        file_path = dataset.file_path
        db_path = dataset.db_path
        dataset.delete()                    # ← primero el registro
        FileService.delete(file_path)       # ← luego el archivo (fallo aquí es recuperable)
        DatabaseService.delete(db_path)     # ← y la BD materializada
        