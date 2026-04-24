from django_rest_framework import serializers


class DatasetUploadSerializer(serializers.Serializer):
    file = serializers.FileField()
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(max_length=1000, default='', allow_blank=True)
    
    
    
    def validate_file(self, file):
        allowed_extensions = ['.csv', '.xlsx', '.json']
        ext = '.' + file.name.split('.')[-1].lower()
        if ext not in allowed_extensions:
            raise serializers.ValidationError(
                f'Formato no soportado: {ext}. Formatos permitidos: {", ".join(allowed_extensions)}'
            )
        max_size_mb = 50
        if file.size > max_size_mb * 1024 * 1024:
            raise serializers.ValidationError(
                f'Archivo demasiado grande: {file.size / (1024 * 1024):.2f} MB. El tamaño máximo permitido es {max_size_mb} MB.'
            )
        return file