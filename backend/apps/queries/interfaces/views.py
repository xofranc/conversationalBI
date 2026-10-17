"""REST adapter for query application use cases; no ORM access is performed."""

import logging

from django.core.exceptions import ImproperlyConfigured
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.pagination import PageNumberPagination
from rest_framework.response import Response
from rest_framework.serializers import IntegerField

from apps.queries.application.dtos import (
    ExecuteQueryInput,
    GetQueryDetailInput,
    ListQueryHistoryInput,
    SubmitFeedbackInput,
)
from apps.queries.application.use_cases import (
    DatasetNotFound,
    DatasetNotReady,
    FeedbackAlreadyExists,
    InvalidFeedbackScoreInput,
    QueryAccessDenied,
    QueryNotFound,
)

from .serializers import (
    FeedbackSerializer,
    QueryHistoryListSerializer,
    QueryHistorySerializer,
    QueryRequestSerializer,
    QueryResponseSerializer,
)

logger = logging.getLogger(__name__)


class QueryHistoryPagination(PageNumberPagination):
    page_size = 20


class QueryViewSet(viewsets.GenericViewSet):
    identity_provider = None
    permission_classes = None
    pagination_class = QueryHistoryPagination

    def initial(self, request, *args, **kwargs):
        if not callable(self.identity_provider):
            raise ImproperlyConfigured(
                "QueryViewSet.identity_provider must be configured by "
                "create_urlpatterns()."
            )
        return super().initial(request, *args, **kwargs)

    def get_use_cases(self):
        return self.use_cases

    def get_serializer_class(self):
        if self.action == "create":
            return QueryRequestSerializer
        if self.action == "list":
            return QueryHistoryListSerializer
        if self.action == "feedback":
            return FeedbackSerializer
        return QueryHistorySerializer

    def create(self, request):
        serializer = QueryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id, _owner = self.identity_provider(request)
        dataset_id = serializer.validated_data["dataset_id"]
        try:
            result = self.get_use_cases()["execute"].execute(ExecuteQueryInput(
                user_id=user_id,
                question=serializer.validated_data["question"],
                dataset_id=dataset_id,
            ))
        except (DatasetNotFound, QueryAccessDenied):
            return Response(
                {"error": "No tienes acceso a este dataset."},
                status=status.HTTP_403_FORBIDDEN,
            )
        except DatasetNotReady as exc:
            return Response(
                {"error": str(exc)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except APIException:
            # Preserve DRF's status and response body for HTTP exceptions from adapters.
            raise
        except Exception:
            logger.exception("Error interno ejecutando consulta (dataset_id=%s)", dataset_id)
            return Response(
                {"error": "Error interno al procesar la consulta."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(QueryResponseSerializer(result).data, status=status.HTTP_200_OK)

    def list(self, request):
        user_id, _owner = self.identity_provider(request)
        raw_dataset_id = request.query_params.get("dataset_id")
        dataset_id = None
        if raw_dataset_id:
            field = IntegerField()
            try:
                dataset_id = field.run_validation(raw_dataset_id)
            except ValidationError:
                raise ValidationError({"dataset_id": "A valid integer is required."})

        entries = self.get_use_cases()["list_history"].execute(
            ListQueryHistoryInput(user_id=user_id, dataset_id=dataset_id)
        )
        page = self.paginate_queryset(entries)
        if page is not None:
            data = QueryHistoryListSerializer(page, many=True).data
            return self.get_paginated_response(data)
        return Response(QueryHistoryListSerializer(entries, many=True).data)

    def retrieve(self, request, pk=None):
        user_id, _owner = self.identity_provider(request)
        try:
            query_id = int(pk)
        except (TypeError, ValueError):
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            detail = self.get_use_cases()["get_detail"].execute(
                GetQueryDetailInput(user_id=user_id, query_id=query_id)
            )
        except QueryNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(QueryHistorySerializer(detail).data)

    @action(detail=True, methods=["post"], url_path="feedback")
    def feedback(self, request, pk=None):
        serializer = FeedbackSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user_id, _owner = self.identity_provider(request)
        try:
            query_id = int(pk)
        except (TypeError, ValueError):
            return Response(status=status.HTTP_404_NOT_FOUND)
        try:
            self.get_use_cases()["submit_feedback"].execute(SubmitFeedbackInput(
                user_id=user_id,
                query_id=query_id,
                score=serializer.validated_data["score"],
                comment=serializer.validated_data.get("comment", ""),
            ))
        except QueryNotFound:
            return Response(status=status.HTTP_404_NOT_FOUND)
        except FeedbackAlreadyExists:
            return Response(
                {"error": "Ya existe feedback para esta consulta."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InvalidFeedbackScoreInput as exc:
            return Response(
                {"score": [str(exc)]},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return Response(status=status.HTTP_201_CREATED)
