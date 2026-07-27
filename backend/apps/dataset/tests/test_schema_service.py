import pandas as pd
from apps.dataset.services import SchemaService

def test_infer_dtype_float():
    s = pd.Series([1.5, 2.3, 3.0])
    assert SchemaService.infer_dtype(s) == "float"

def test_infer_dtype_date():
    s = pd.Series(["2024-01-01", "2024-06-15"])
    assert SchemaService.infer_dtype(s) == "date"

def test_infer_dtype_date_mixed_formats_sin_warning(recwarn):
    """Formatos mezclados: se infiere 'date' sin UserWarning de pandas 2.x."""
    s = pd.Series(["2024-01-01", "15/06/2024", "Jan 3, 2024"])
    assert SchemaService.infer_dtype(s) == "date"
    assert not [w for w in recwarn.list if issubclass(w.category, UserWarning)]

def test_parse_column_nullable():
    s = pd.Series([1, None, 3])
    result = SchemaService._parse_column("monto", s)
    assert result["nullable"] is True
    assert result["dtype"] == "float"