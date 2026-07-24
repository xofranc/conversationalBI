import os
from rest_framework import serializers


class DatasetUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000, default='', allow_blank=True)
    
    
    
    def validate_file(self, file):
        allowed_extensions = ['.csv', '.xlsx', '.json']
        allowed_content_types = [
            'text/csv',
            'application/csv',
            'application/vnd.ms-excel',
            'application/json',
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        ]

        ext = os.path.splitext(file.name)[1].lower().strip()

        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f'Formato no soportado: {ext}. Formatos permitidos: {", ".join(allowed_extensions)}'
            )

        content_type = getattr(file, 'content_type', '')

        if content_type and content_type not in allowed_content_types:
            raise serializers.ValidationError(
                f'Tipo de contenido no soportado: {content_type}'
            )

        max_size_mb = 50

        if file.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(
                f'Archivo demasiado grande: {file.size / (1024 * 1024):.2f} MB. El tamaño máximo permitido es {max_size_mb} MB.'
            )

        return file