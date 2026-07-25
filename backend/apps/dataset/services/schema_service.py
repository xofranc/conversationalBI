import json
import os

import pandas as pd


class SchemaService:
    
    @staticmethod
    
    def extract(abs_path: str) -> dict:
        
        """
        Recibe ruta absoluta, retorna schema json completo
        """
        
        ext = os.path.splitext(abs_path)[1].lower()
        
        sheets = SchemaService.read_tables(abs_path, ext)
        
        return {
            "tables": [
                SchemaService._parse_table(name, df) for name, df in sheets.items()
            ]
        }
        
        
    @staticmethod
    def read_tables(abs_path: str, ext: str) -> dict:
        """
        Única función de carga de archivos del sistema.
        Compartida por SchemaService (extracción de schema) y
        SQLExecutor (carga al sandbox SQLite) — nunca divergen.
        Retorna {nombre_tabla: DataFrame}.
        """
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

        if ext in ('.xlsx', '.xls'):
            xls = pd.ExcelFile(abs_path)
            return {name: xls.parse(name) for name in xls.sheet_names}

        raise ValueError(f"Extensión no soportada: {ext}")

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
            "dtype":    SchemaService.infer_dtype(series),
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
    def infer_dtype(series: pd.Series) -> str:
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