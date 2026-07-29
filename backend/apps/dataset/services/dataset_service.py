import os
from django.conf import settings

from apps.dataset.repositories import DatasetRepository
from ..models import Dataset
from .database_service import DatabaseService
from .file_service import FileService
from .schema_service import SchemaService


class DatasetService:
    
    """
        Orquesta, Solo coordina, no tiene logica de archivos 
        ni de pandas directamente
    """
    
    @staticmethod
    def create(file, user, name: str, description: str = "") -> Dataset:
        FileService.validate(file)
        
        
        dataset = DatasetRepository.create_dataset(
            user=user,
            name=name,
            description=description,
            file_size=file.size
        )
        
        try:
            dataset.status = Dataset.Status.PROCESSING
            dataset.file_path = FileService.save(file, user.id)
            dataset.save(update_fields=["status", "file_path", "updated_at"])

            abs_path = os.path.join(settings.MEDIA_ROOT, dataset.file_path)

            # Materializa la BD SQLite persistente: las consultas y los
            # análisis se ejecutan contra ella, sin releer el archivo.
            dataset.db_path = DatabaseService.materialize(dataset.id, abs_path)
            dataset.save(update_fields=["db_path", "updated_at"])

            schema = SchemaService.extract(abs_path)
            row_count = sum(t["row_count"] for t in schema["tables"])
            col_count = sum(len(t["columns"]) for t in schema["tables"])

            for tabla_data in schema["tables"]:
                DatasetRepository.create_table(dataset, tabla_data)

            dataset.mark_ready(schema, row_count, col_count) 
            
        except Exception as exc:
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
        