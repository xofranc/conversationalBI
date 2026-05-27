from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from .serializers.datasetUpload import DatasetUploadSerializer
from .serializers.datasetList import DatasetListSerializer
from .serializers.datasetDetail import DatasetDetailSerializer
from .services import DatasetService
from .permissions import IsDatasetOwner
from .models import Dataset


class DatasetViewSet(viewsets.GenericViewSet):
    
    """
    ViewSet principal de datasets.

    Acciones disponibles:
        POST   /datasets/          → upload (create)
        GET    /datasets/          → listado del usuario (list)
        GET    /datasets/{id}/     → detalle (retrieve)
        DELETE /datasets/{id}/     → eliminar (destroy)
        GET    /datasets/{id}/schema/ → solo el schema_json (action custom)
        
    """
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    #! Queryset base: siempre es filtrado por el usuario
    
    def get_queryset(self):
        return Dataset.objects.filter(
            user=self.request.user
        ).prefetch_related('tables')
        
    #! Serializer dinamico segun la accion
    def get_serializer_class(self):
        if self.action == 'create':
            return DatasetUploadSerializer
        if self.action == 'list':
            return DatasetListSerializer
        return DatasetDetailSerializer
    

    #! Permisos dinamicos segun la accion 
    def get_permissions(self):
        if self.action in ('retrieve', 'destroy', "schema"):
            return [IsAuthenticated(), IsDatasetOwner()]
        return [IsAuthenticated()]
    
    #! POST /datasets/ → upload de un nuevo dataset
    
    def create(self,request):
        serializer = DatasetUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        try:
            dataset = DatasetService.create(
                file        = serializer.validated_data['file'],
                user        = request.user,
                name        = serializer.validated_data['name'],
                description = serializer.validated_data.get('description', ''),
            )
        except ValueError as e:                          
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:                           
            return Response(
                {'error': 'Error al procesar el archivo.' + str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(
            DatasetDetailSerializer(dataset).data,       
            status=status.HTTP_201_CREATED
        )
        
    #! GET /datasets/ → listado de datasets del usuario    
    def list (self, request):
        queryset = self.get_queryset()
        serializer = DatasetListSerializer(queryset, many=True)
        return Response(serializer.data)
    
    #! GET /datasets/{id}/ → detalle del dataset
    def retrieve(self, request, pk=None):
        dataset = self.get_object()
        serializer = DatasetDetailSerializer(dataset)
        return Response(serializer.data)
    
    #! DELETE /datasets/{id}/ → eliminar el dataset
    def destroy(self, request, pk=None):
        dataset = self.get_object()

        try: 
            DatasetService.delete(dataset.id, request.user)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
            
        return Response(status=status.HTTP_204_NO_CONTENT)
    
    
    #! GET /datasets/{id}/schema/ → solo el schema_json del dataset
    @action(detail=True, methods=['get'], url_path='schema')
    def schema(self, request, pk=None):
        
        '''
        endpoint especificio para que el engine consuma el schema sin 
        cargar el dataset completo con tablas
        '''
        
        dataset = self.get_object()
        
        return Response({
            'schema_json': dataset.schema_json,
            'id': dataset.id,
            'name': dataset.name,
            'row_count': dataset.row_count
        })
        