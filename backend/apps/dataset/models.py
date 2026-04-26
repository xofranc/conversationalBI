from django.db import models
from django.db.models import ForeignKey
from django.conf import settings


# Create your models here.
class Dataset(models.Model):
    
    class Status(models.TextChoices):
        READY = 'ready', 'Ready'
        INACTIVE = 'inactive', 'Inactive'
        ERROR = 'error', 'Error'
        PROCESSING = 'processing', 'Processing'
        UPLOADED = 'uploaded', 'Uploaded'
        
        
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='datasets'
    )
    
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    #! RUta de acceso al archivo subido
    file_path = models.CharField(max_length=500)
    file_size = models.BigIntegerField(default=0)
    
    #! contrato con el dataset, con ai engine
    schema_json = models.JSONField(default=dict)
    
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PROCESSING
    )
    
    error_msg  = models.TextField(blank = True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'status']),
        ]
        
    def __str__(self):
        return f"{self.name} ({self.status})"
    
    def mark_ready(self, schema: dict, row_count: int) -> None:
        """Transición atómica a estado ready."""
        self.schema_json = schema
        self.row_count   = row_count
        self.status      = self.Status.READY
        self.save(update_fields=["schema_json", "row_count", "status", "updated_at"])

    def mark_error(self, message: str) -> None:
        """Transición atómica a estado error."""
        self.status    = self.Status.ERROR
        self.error_msg = message
        self.save(update_fields=["status", "error_msg", "updated_at"])

    
class DatasetTable(models.Model):
    
    '''
        Una hoja de excel o una tabla dentro de un dataset.
        para CSVs siempre habra exactamente una tabla
    '''
    
    dataset = models.ForeignKey(
        Dataset,
        on_delete=models.CASCADE,
        related_name='tables'
    )
    
    
    table_name = models.CharField(max_length=255)
    row_count = models.IntegerField(default=0)
    column_count = models.IntegerField(default=0)
    
    columns_json = models.JSONField(default=list)  #! Lista de nombres de columnas y tipos inferidos
    
    '''
     Estructura: [{"name": "fecha", "dtype": "date",
                   "nullable": false, "sample": ["2024-01-01"]}]
    '''
    
    class Meta: 
        unique_together = ('dataset', 'table_name')
        ordering = ['table_name']
        
    def __str__(self):
        return f"{self.dataset.name} / {self.table_name}"
    
    
    
        '''
                    Estructura esperada de schema_json en Dataset
            SCHEMA_JSON_EXAMPLE = {
                "tables": [
                    {
                        "name": "ventas",
                        "row_count": 12450,
                        "columns": [
                            {
                                "name": "fecha",
                                "dtype": "date",       # int | float | str | date | bool
                                "nullable": False,
                                "sample": ["2024-01-15", "2024-02-03", "2024-03-10"]
                            },
                            {
                                "name": "monto",
                                "dtype": "float",
                                "nullable": False,
                                "sample": [150000.0, 89000.5, 230000.0]
                            },
                            {
                                "name": "region",
                                "dtype": "str",
                                "nullable": True,
                                "sample": ["Bogota", "Medellin", "Cali"]
                            },
                        ]
                    }
                ]
            }
        '''
                