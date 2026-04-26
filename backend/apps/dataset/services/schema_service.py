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
        if ext == ".csv":
            return {"main": pd.read_csv(abs_path)}
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
            "sample":   series.dropna().drop_duplicates().head(5).tolist(),
        }

    @staticmethod
    def _infer_dtype(series: pd.Series) -> str:
        kind = series.dtype.kind
        mapping = {"i": "int", "u": "int", "f": "float", "b": "bool", "M": "date"}
        if kind in mapping:
            return mapping[kind]
        if series.dtype == object:
            try:
                pd.to_datetime(series.dropna().head(20), infer_datetime_format=True)
                return "date"
            except Exception:
                pass
        return "str"