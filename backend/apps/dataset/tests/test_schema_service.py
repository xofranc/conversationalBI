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

def test_column_info_str_baja_cardinalidad_lista_valores():
    import pandas as pd
    from apps.dataset.services.schema_service import SchemaService
    s = pd.Series(['Bogotá', 'Cali', 'Bogotá', 'Cali', 'Bogotá'])
    info = SchemaService._column_info('str', s)
    assert 'Bogotá' in info and 'Cali' in info


def test_column_info_str_alta_cardinalidad_no_lista():
    import pandas as pd
    from apps.dataset.services.schema_service import SchemaService
    s = pd.Series([f'valor_{i}' for i in range(500)])
    info = SchemaService._column_info('str', s)
    assert 'valores:' not in info
    assert '500 valores distintos' in info


def test_column_info_fecha_da_rango():
    import pandas as pd
    from apps.dataset.services.schema_service import SchemaService
    s = pd.Series(['2024-01-15', '2024-06-20', '2024-03-10'])
    info = SchemaService._column_info('date', s)
    assert '2024-01-15' in info
    assert '2024-06-20' in info


def test_column_info_numerica_da_rango():
    import pandas as pd
    from apps.dataset.services.schema_service import SchemaService
    s = pd.Series([10, 500, 100])
    info = SchemaService._column_info('int', s)
    assert '10' in info and '500' in info
