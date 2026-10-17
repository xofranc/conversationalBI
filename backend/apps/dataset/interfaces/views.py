"""REST adapter for dataset use cases; no ORM access is performed here."""

import logging

from django.core.exceptions import ImproperlyConfigured
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.dataset.application.dtos import (
    CreateDatasetInput,
    DeleteDatasetInput,
    GetDatasetInput,
    ListDatasetsInput,
)
from apps.dataset.application.use_cases import (
    DatasetAccessDenied,
    DatasetNotFound,
    DatasetUploadRejected,
)

from .serializers import (
    DatasetDetailSerializer,
    DatasetListSerializer,
    DatasetUploadSerializer,
)

logger = logging.getLogger(__name__)


class DatasetViewSet(viewsets.GenericViewSet):
    identity_provider = None
    permission_classes = None
    parser_classes = [MultiPartParser, FormParser]
    # The historical list endpoint returned a bare array, without pagination.
    pagination_class = None

    def initial(self, request, *args, **kwargs):
        if not callable(self.identity_provider):
            raise ImproperlyConfigured(
                "DatasetViewSet.identity_provider must be configured by "
                "create_urlpatterns()."
            )
        return super().initial(request, *args, **kwargs)

    def get_use_cases(self):
        return self.use_cases

    def get_serializer_class(self):
        if self.action == "create":
            return DatasetUploadSerializer
        if self.action == "list":
            return DatasetListSerializer
        return DatasetDetailSerializer

    def create(self, request):
        serializer = DatasetUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        uploaded_file = serializer.validated_data["file"]
        user_id, owner = self.identity_provider(request)
        try:
            dto = self.get_use_cases()["create"].execute(CreateDatasetInput(
                user_id=user_id,
                name=serializer.validated_data["name"],
                filename=uploaded_file.name,
                content=uploaded_file.read(),
                description=serializer.validated_data.get("description", ""),
            ))
        except DatasetUploadRejected as error:
            return Response({"file": [str(error)]}, status=status.HTTP_400_BAD_REQUEST)
        except ValueError as error:
            return Response({"error": str(error)}, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception("Error procesando upload de dataset (user_id=%s)", user_id)
            return Response(
                {"error": "Error al procesar el archivo."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(
            DatasetDetailSerializer(dto, context={"owner": owner}).data,
            status=status.HTTP_201_CREATED,
        )

    def list(self, request):
        user_id, _owner = self.identity_provider(request)
        dtos = self.get_use_cases()["list"].execute(ListDatasetsInput(user_id=user_id))
        return Response(DatasetListSerializer(dtos, many=True).data)

    def retrieve(self, request, pk=None):
        return self._get_dataset_response(request, pk, detail=True)

    def destroy(self, request, pk=None):
        user_id, _owner = self.identity_provider(request)
        try:
            self.get_use_cases()["delete"].execute(
                DeleteDatasetInput(user_id=user_id, dataset_id=self._dataset_id(pk))
            )
        except (DatasetNotFound, DatasetAccessDenied, ValueError):
            # Legacy get_object() filtered by owner and returned 404 for both.
            return Response(status=status.HTTP_404_NOT_FOUND)
        except Exception:
            logger.exception("Error eliminando dataset %s", pk)
            return Response(
                {"error": "Error al eliminar el dataset."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=["get"], url_path="schema")
    def schema(self, request, pk=None):
        response = self._get_dataset_response(request, pk, detail=False)
        return response

    @staticmethod
    def _dataset_id(pk):
        return int(pk)

    def _get_dataset_response(self, request, pk, *, detail):
        user_id, owner = self.identity_provider(request)
        try:
            dto = self.get_use_cases()["get"].execute(
                GetDatasetInput(user_id=user_id, dataset_id=self._dataset_id(pk))
            )
        except (DatasetNotFound, DatasetAccessDenied, ValueError):
            return Response(status=status.HTTP_404_NOT_FOUND)

        if detail:
            return Response(DatasetDetailSerializer(dto, context={"owner": owner}).data)
        return Response({
            "schema_json": dto.schema,
            "id": dto.id,
            "name": dto.name,
            "row_count": dto.row_count,
        })
