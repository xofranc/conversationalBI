
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import QueryHistory, QueryFeedback
from .serializers import (
    QueryRequestSerializer,
    QueryHistorySerializer,
    FeedbackSerializer,
)
from .services import QueryService
from apps.users.services import UserService
from rest_framework.mixins import CreateModelMixin

class QueryViewSet(viewsets.GenericViewSet, CreateModelMixin):
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return QueryHistory.objects.filter(
            user=self.request.user
        ).select_related('result')

    # ── POST /queries/ ────────────────────────────────────────────────────
    def create(self, request):
        serializer = QueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user       = request.user
        question   = serializer.validated_data['question']
        dataset_id = serializer.validated_data['dataset_id']

        ''' 
        Guard de cuota antes de ejecutar la consulta 
        
        Tener en cuenta mas adelante, para la implementación de planes, que quizás queramos diferenciar entre tipos de consultas (ej: consultas simples vs consultas con gráficos) y asignarles diferentes costos. Por ahora, todas las consultas cuentan igual para la cuota.
        
        if not UserService.can_query(user):
            return Response(
                {'error': 'Has alcanzado el límite de consultas de tu plan.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS
            )
            
            
        '''
        # Guard de acceso al dataset
        if not UserService.can_access_dataset(user, dataset_id):
            return Response(
                {'error': 'No tienes acceso a este dataset.'},
                status=status.HTTP_403_FORBIDDEN
            )

        try:
            result = QueryService.execute(question, dataset_id, user)
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        return Response(result, status=status.HTTP_200_OK)

    # ── GET /queries/ → historial ─────────────────────────────────────────
    def list(self, request):
        dataset_id = request.query_params.get('dataset_id')
        qs         = self.get_queryset()
        if dataset_id:
            qs = qs.filter(dataset_id=dataset_id)
        serializer = QueryHistorySerializer(qs, many=True)
        return Response(serializer.data)

    # ── GET /queries/{id}/ → detalle ──────────────────────────────────────
    def retrieve(self, request, pk=None):
        try:
            query = QueryHistory.objects.select_related('result').get(
                pk=pk, user=request.user
            )
        except QueryHistory.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(QueryHistorySerializer(query).data)

    # ── POST /queries/{id}/feedback/ ──────────────────────────────────────
    @action(detail=True, methods=['post'], url_path='feedback')
    def feedback(self, request, pk=None):
        try:
            query = QueryHistory.objects.get(pk=pk, user=request.user)
        except QueryHistory.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

        if hasattr(query, 'feedback'):
            return Response(
                {'error': 'Ya existe feedback para esta consulta.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        QueryFeedback.objects.create(
            query   = query,
            score   = serializer.validated_data['score'],
            comment = serializer.validated_data.get('comment', ''),
        )
        return Response(status=status.HTTP_201_CREATED)