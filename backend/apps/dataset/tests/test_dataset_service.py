from unittest.mock import patch, MagicMock
from apps.dataset.services import DatasetService
import pytest
@patch("apps.datasets.services.dataset_service.SchemaService.extract")
@patch("apps.datasets.services.dataset_service.FileService.save")
@patch("apps.datasets.services.dataset_service.FileService.validate")
def test_create_marks_error_on_schema_failure(mock_validate, mock_save, mock_extract, db):
    mock_save.return_value = "datasets/test.csv"
    mock_extract.side_effect = Exception("Archivo corrupto")

    file = MagicMock()
    file.name = "datos.csv"
    file.size = 1024
    user = ...  # fixture de pytest-django

    with pytest.raises(Exception, match="Archivo corrupto"):
        DatasetService.create(file, user, "Test")

    # Verifica que el dataset quedó en estado error, no en limbo
    from apps.dataset.models import Dataset
    ds = Dataset.objects.get(name="Test")
    assert ds.status == "error"
    assert "corrupto" in ds.error_msg

