# apps/queries/serializers/query_request.py
from rest_framework import serializers


class QueryRequestSerializer(serializers.Serializer):
    question   = serializers.CharField(
                   min_length = 5,
                   max_length = 500,
                   error_messages = {
                       'min_length': 'La pregunta debe tener al menos 5 caracteres.',
                       'blank':      'La pregunta no puede estar vacía.',
                   }
                 )
    dataset_id = serializers.IntegerField(min_value=1)

    def validate_question(self, value):
        # Evita preguntas que claramente son inyecciones SQL
        forbidden = ['drop', 'delete', 'truncate', 'insert', 'update', 'alter']
        lower     = value.lower()
        for word in forbidden:
            if word in lower:
                raise serializers.ValidationError(
                    f"La pregunta contiene una palabra no permitida: '{word}'."
                )
        return value.strip()