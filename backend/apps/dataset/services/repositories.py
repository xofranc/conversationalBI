from ..models import Dataset, DatasetTable


class DatasetRepository:
    
    @staticmethod
    def create_dataset(user,
                       name: str,
                       description: str,
                       file_size: int) -> Dataset:
        
        return Dataset.objects.create(
            user=user,
            name=name,
            description=description,
            file_size=file_size,
            status=Dataset.Status.UPLOADED
        )
    
    @staticmethod
    def get_by_id(dataset_id: int) -> Dataset:
        return Dataset.objects.select_related('user').get(id=dataset_id)
    
    @staticmethod
    def get_by_user(user) -> list:
        return Dataset.objects.filter(user=user).order_by('-created_at')
    
    @staticmethod
    def get_schema(dataset_id: int) -> dict:
         """Usado por ai_engine para obtener el schema sin cargar todo el objeto."""
         return Dataset.objects.values('schema_json').get(pk=dataset_id)['schema_json']
     
     
    @staticmethod
    def create_table(dataset: Dataset, table_data: dict) -> DatasetTable:
        return DatasetTable.objects.create(
            dataset      = dataset,
            table_name   = table_data["name"],
            row_count    = table_data["row_count"],
            column_count = len(table_data["columns"]),
            columns_json = table_data["columns"],
        )
        