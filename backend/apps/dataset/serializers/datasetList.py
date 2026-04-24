from rest_framework import serializers
from .models import Dataset


class DatasetListSerializer(serializers.ModelSerializer):
    """
    Versión ligera para el listado. No incluye schema_json ni tablas
    para no sobrecargar la respuesta cuando hay muchos datasets.
    """
    class Meta:
        model  = Dataset
        fields = [
            'id',
            'name',
            'description',
            'file_size',
            'row_count',
            'column_count',
            'status',
            'created_at',
        ]
        read_only_fields = fields
