from .repositories import DatasetRepository
from ..models import Dataset
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
            
            schema = SchemaService.extract(dataset.file_path)
            row_count = sum(t["row_count"] for t in schema["tables"])
            
            for tabla_data in schema["tables"]:
                DatasetRepository.create_table(dataset, tabla_data)
                
            dataset.mark_ready(schema, row_count)
            
        except Exception as exc:
            dataset.mark_error(str(exc))
            raise
        
        return dataset
    
    @staticmethod
    def delete(dataset_id: int, user) -> None:
        dataset = DatasetRepository.get_by_id(dataset_id)
        if dataset.user!= user:
            raise PermissionError("No tienes permiso para eliminar este dataset.")
        FileService.delete(dataset.file_path)
        dataset.delete()