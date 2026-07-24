import json

import pandas as pd
import os
from django.conf import settings


class SchemaService:
    
    @staticmethod
    
    def extract(file_path: str) -> dict:
        
        """
        Recibe ruta relativa, retorna schema json completo
        """
        
        abs_path = os.path.join(settings.MEDIA_ROOT, file_path)
        ext = os.path.splitext(file_path)[1].lower()
        
        sheets = SchemaService._read_file(abs_path, ext)
        
        return {
            "tables": [
                SchemaService._parse_table(name, df) for name, df in sheets.items()
            ]
        }
        
        
    @staticmethod
    def _read_file(abs_path: str, ext: str) -> dict:
        if ext == '.csv':
            return {"main": pd.read_csv(abs_path)}

        if ext == '.json':
            with open(abs_path) as f:
                raw = json.load(f)          # leer como Python nativo primero

            # JSON con múltiples tablas: {"ventas": [...], "productos": [...]}
            if isinstance(raw, dict) and all(isinstance(v, list) for v in raw.values()):
                return {k: pd.DataFrame(v) for k, v in raw.items()}

            # JSON con array de registros: [{"col": val}, ...]
            return {"main": pd.DataFrame(raw)}

        # Excel — sin cambios
        xls = pd.ExcelFile(abs_path)
        return {name: xls.parse(name) for name in xls.sheet_names}

    @staticmethod
    def _parse_table(name: str, df: pd.DataFrame) -> dict:
        return {
            "name":      name,
            "row_count": len(df),
            "columns": [
                SchemaService._parse_column(col, df[col])
                for col in df.columns
            ],
        }

    @staticmethod
    def _parse_column(col_name: str, series: pd.Series) -> dict:
        return {
            "name":     str(col_name),
            "dtype":    SchemaService._infer_dtype(series),
            "nullable": bool(series.isnull().any()),
            "sample":   SchemaService._safe_sample(series),
        }

    @staticmethod
    def _safe_sample(series: pd.Series) -> list:
        """Convierte la muestra a tipos nativos de Python, JSON-seguros."""
        raw = series.dropna().drop_duplicates().head(5)
        result = []
        for val in raw:
            if hasattr(val, 'isoformat'):          # datetime, date, Timestamp
                result.append(val.isoformat())
            elif hasattr(val, 'item'):             # numpy int64, float64, bool_
                result.append(val.item())
            else:
                result.append(val)
        return result
    
    @staticmethod
    def _infer_dtype(series: pd.Series) -> str:
        kind = series.dtype.kind
        mapping = {"i": "int", "u": "int", "f": "float", "b": "bool", "M": "date"}
        if kind in mapping:
            return mapping[kind]
        if series.dtype == object:
            try:
                pd.to_datetime(series.dropna().head(20))
                return "date"
            except Exception:
                pass
        return "str"