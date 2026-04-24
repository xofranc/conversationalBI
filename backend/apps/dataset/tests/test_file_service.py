import pytest
from unittest.mock import MagicMock
from apps.dataset.services import FileService

def test_validate_rejects_pdf():
    file = MagicMock()
    file.name = "reporte.pdf"
    file.size = 1024
    with pytest.raises(ValueError, match="Formato no soportado"):
        FileService.validate(file)

def test_validate_rejects_oversized_file():
    file = MagicMock()
    file.name = "datos.csv"
    file.size = 60 * 1024 * 1024  # 60 MB
    with pytest.raises(ValueError, match="pesa"):
        FileService.validate(file)