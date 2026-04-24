from rest_framework import serializers
from .models import DatasetTable


class DatasetTableSerializer(serializers.ModelSerializer):
    
    class Meta: 
        model = DatasetTable
        fields = [
            'id',
            'table_name',
            'row_count',
            'column_count',
            'columns_json',
        ]
        
        read_only_fields = fields