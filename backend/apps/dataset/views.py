import logging

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
from apps.core.permissions import IsAuthenticatedOrDemo
from apps.core.services.demo_service import DemoService

logger = logging.getLogger(__name__)


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
    
    permission_classes = [IsAuthenticatedOrDemo]
    parser_classes = [MultiPartParser, FormParser]
    
    #! Queryset base: siempre es filtrado por el usuario
    
    def get_queryset(self):
        # En modo demo, filtrar por session_id
        session_id = self.request.headers.get('X-Session-ID')
        if session_id:
            user = DemoService.get_demo_user(session_id)
            return Dataset.objects.filter(user=user).prefetch_related('tables')
        
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
            return [IsAuthenticatedOrDemo()]
        return [IsAuthenticatedOrDemo()]
    

    #! POST /datasets/ → upload de un nuevo dataset
    
    def create(self,request):
        logger.info('=== UPLOAD INICIO ===')
        logger.info('Headers: session_id=%s, content_type=%s', request.headers.get('X-Session-ID'), request.content_type)

        serializer = DatasetUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file = serializer.validated_data['file']
        name = serializer.validated_data['name']
        logger.info('Archivo validado: name=%s, size=%s, content_type=%s', file.name, file.size, getattr(file, 'content_type', 'N/A'))
        
        # Obtener usuario (autenticado o demo)
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            user = DemoService.get_demo_user(session_id)
            logger.info('Modo demo: session_id=%s, user_id=%s, email=%s', session_id, user.id, user.email)
        else:
            user = request.user
            logger.info('Modo auth: user_id=%s', user.id)
        
        try:
            dataset = DatasetService.create(
                file        = file,
                user        = user,
                name        = name,
                description = serializer.validated_data.get('description', ''),
            )
        except ValueError as e:                          
            logger.warning('Upload rechazado (ValueError): %s', e)
            return Response(
                {'error': str(e)},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception:
            logger.exception('Error procesando upload de dataset (user_id=%s, file=%s)', user.id, file.name)
            return Response(
                {'error': 'Error al procesar el archivo.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        logger.info('=== UPLOAD OK === dataset_id=%s, name=%s', dataset.id, dataset.name)
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

        # Obtener usuario (autenticado o demo)
        session_id = request.headers.get('X-Session-ID')
        if session_id:
            user = DemoService.get_demo_user(session_id)
        else:
            user = request.user

        try: 
            DatasetService.delete(dataset.id, user)
        except PermissionError as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_403_FORBIDDEN
            )
        except Exception:
            logger.exception('Error eliminando dataset %s', dataset.id)
            return Response(
                {'error': 'Error al eliminar el dataset.'},
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