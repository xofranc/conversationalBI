from rest_framework import serializers
from .datasetTable import DatasetTableSerializer
from ..models import Dataset



class DatasetDetailSerializer(serializers.ModelSerializer):
    tables = DatasetTableSerializer(many=True, read_only=True)
    owner = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = Dataset
        fields = [
            'id',
            'owner',
            'name',
            'description',
            'file_size',
            'row_count',
            'column_count',
            'status',
            'error_msg',
            'schema_json',
            'tables',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields