"""Motor pandas para análisis estadísticos sobre tablas materializadas.

El módulo solo conoce DataFrames y dependencias explícitas: no importa Django
ni servicios de infraestructura.
"""

from __future__ import annotations

import re
from collections.abc import Callable

import pandas as pd
from pandas.tseries.frequencies import to_offset


class AnalysisError(Exception):
    """Los datos no permiten realizar el análisis solicitado."""


def _json_safe(value):
    """Normaliza valores pandas/numpy a tipos JSON-serializables."""
    if value is None or pd.isna(value):
        return None
    if hasattr(value, "isoformat"):
        return value.isoformat()
    if hasattr(value, "item"):
        return value.item()
    return value


def _columns_meta(rows: list, infer_dtype: Callable[[pd.Series], str]) -> list:
    if not rows:
        return []
    frame = pd.DataFrame(rows)
    return [
        {"name": column, "dtype": infer_dtype(frame[column])}
        for column in frame.columns
    ]


def _dtypes(frame: pd.DataFrame, infer_dtype: Callable[[pd.Series], str]) -> dict:
    return {column: infer_dtype(frame[column]) for column in frame.columns}


def _es_id(frame: pd.DataFrame, column) -> bool:
    """Identifica columnas ID por nombre o por su forma autoincremental."""
    name = str(column).lower()
    if name == "id" or name.startswith("id_") or name.endswith("_id"):
        return True
    series = frame[column]
    return (
        series.dtype.kind in "iu"
        and series.nunique() == len(series)
        and series.is_monotonic_increasing
    )


def _numeric_cols(frame: pd.DataFrame, dtypes: dict) -> list:
    columns = [column for column, dtype in dtypes.items() if dtype in ("int", "float")]
    without_ids = [column for column in columns if not _es_id(frame, column)]
    return without_ids or columns


def _pick_table(tables: dict, predicate, error_message: str) -> pd.DataFrame:
    for frame in tables.values():
        if predicate(frame):
            return frame
    raise AnalysisError(error_message)


def _mentioned_column(question: str, candidates: list):
    normalized = question.lower()
    for column in candidates:
        if re.search(rf"\b{re.escape(str(column).lower())}\b", normalized):
            return column
    return None


def forecast(tables: dict, question: str, infer_dtype, limits) -> dict:
    frame = _pick_table(
        tables,
        lambda data: any(
            dtype == "date" for dtype in _dtypes(data, infer_dtype).values()
        ) and _numeric_cols(data, _dtypes(data, infer_dtype)),
        "Para pronosticar necesito una columna de fechas y una numérica en el mismo archivo.",
    )
    dtypes = _dtypes(frame, infer_dtype)
    date_column = next(column for column, dtype in dtypes.items() if dtype == "date")
    numeric_columns = _numeric_cols(frame, dtypes)
    value_column = _mentioned_column(question, numeric_columns) or max(
        numeric_columns, key=lambda column: frame[column].var(skipna=True)
    )

    series = (
        frame[[date_column, value_column]]
        .assign(
            **{
                date_column: pd.to_datetime(
                    frame[date_column], format="mixed", errors="coerce"
                )
            }
        )
        .dropna()
        .groupby(date_column)[value_column]
        .sum()
        .sort_index()
    )
    if len(series) < 3:
        raise AnalysisError("La columna de fechas tiene muy pocos puntos con datos.")

    rule = _freq_rule(series.index)
    series = series.resample(rule).sum()
    if len(series) > limits.max_history_periods:
        series = series.iloc[-limits.max_history_periods :]
    if len(series) < limits.min_forecast_periods:
        raise AnalysisError(
            f"Se necesitan al menos {limits.min_forecast_periods} períodos con datos "
            f"para pronosticar (hay {len(series)})."
        )

    from statsmodels.tsa.holtwinters import ExponentialSmoothing

    try:
        fit = ExponentialSmoothing(series, trend="add", seasonal=None).fit(
            optimized=True
        )
    except Exception as exc:
        raise AnalysisError(f"No se pudo ajustar el modelo de pronóstico: {exc}") from exc

    prediction = fit.forecast(limits.forecast_horizon).clip(lower=0)
    sigma = float((series - fit.fittedvalues).std())
    future = pd.date_range(
        series.index[-1] + to_offset(rule),
        periods=limits.forecast_horizon,
        freq=rule,
    )
    rows = [
        {
            "fecha": index.date().isoformat(),
            value_column: _json_safe(round(value, 2)),
            "tipo": "real",
            "inferior": None,
            "superior": None,
        }
        for index, value in series.items()
    ]
    rows += [
        {
            "fecha": index.date().isoformat(),
            value_column: _json_safe(round(prediction.iloc[position], 2)),
            "tipo": "pronóstico",
            "inferior": _json_safe(
                round(max(0.0, prediction.iloc[position] - 1.96 * sigma), 2)
            ),
            "superior": _json_safe(round(prediction.iloc[position] + 1.96 * sigma, 2)),
        }
        for position, index in enumerate(future)
    ]
    return {
        "rows": rows,
        "columns": _columns_meta(rows, infer_dtype),
        "chart_type": "forecast",
        "chart_config": {"xKey": "fecha", "yKey": value_column, "splitKey": "tipo"},
        "method": f"ExponentialSmoothing(trend='add') sobre '{value_column}' agrupado por {rule}",
    }


def _freq_rule(index: pd.DatetimeIndex) -> str:
    days = pd.Series(index).diff().median().total_seconds() / 86400
    if days <= 1.5:
        return "D"
    if days <= 9:
        return "W"
    if days <= 45:
        return "ME"
    if days <= 100:
        return "QE"
    return "YE"


def anomaly(tables: dict, question: str, infer_dtype, limits) -> dict:
    frame = _pick_table(
        tables,
        lambda data: bool(_numeric_cols(data, _dtypes(data, infer_dtype))),
        "Para detectar anomalías necesito al menos una columna numérica.",
    )
    dtypes = _dtypes(frame, infer_dtype)
    numeric_columns = _numeric_cols(frame, dtypes)
    data = frame.dropna(subset=numeric_columns)
    if len(data) < limits.min_anomaly_rows:
        raise AnalysisError(
            f"Se necesitan al menos {limits.min_anomaly_rows} filas completas para detectar anomalías (hay {len(data)})."
        )

    if len(numeric_columns) == 1:
        column = numeric_columns[0]
        median = data[column].median()
        mad = (data[column] - median).abs().median() or 1e-9
        z_score = 0.6745 * (data[column] - median).abs() / mad
        mask = z_score > 3.5
        scores = z_score[mask]
        method = f"z-score robusto (mediana/MAD) sobre '{column}'"
    else:
        from sklearn.ensemble import IsolationForest

        classifier = IsolationForest(
            n_estimators=100, contamination=0.05, random_state=42
        )
        flags = classifier.fit_predict(data[numeric_columns])
        mask = flags == -1
        scores = -classifier.score_samples(data[numeric_columns])[mask]
        method = f"IsolationForest sobre {len(numeric_columns)} columnas numéricas"

    outliers = data[mask].assign(_score=scores).sort_values("_score", ascending=False)
    if outliers.empty:
        raise AnalysisError("No encontré anomalías: los datos son bastante homogéneos.")

    keep = list(frame.columns)[:6]
    rows = [
        {
            **{column: _json_safe(row[column]) for column in keep},
            "score_anomalia": _json_safe(round(row["_score"], 3)),
        }
        for _, row in outliers.head(limits.max_anomalies).iterrows()
    ]
    x_key = numeric_columns[0]
    y_key = numeric_columns[1] if len(numeric_columns) > 1 else "score_anomalia"
    return {
        "rows": rows,
        "columns": _columns_meta(rows, infer_dtype),
        "chart_type": "anomaly",
        "chart_config": {"xKey": x_key, "yKey": y_key},
        "method": method,
    }


def segment(tables: dict, question: str, infer_dtype, limits) -> dict:
    frame = _pick_table(
        tables,
        lambda data: len(_numeric_cols(data, _dtypes(data, infer_dtype))) >= 2,
        "Para segmentar necesito al menos dos columnas numéricas.",
    )
    dtypes = _dtypes(frame, infer_dtype)
    numeric_columns = _numeric_cols(frame, dtypes)
    pair = sorted(
        numeric_columns,
        key=lambda column: frame[column].var(skipna=True),
        reverse=True,
    )[:2]
    x_column, y_column = pair
    data = frame.dropna(subset=pair).reset_index(drop=True)
    if len(data) < limits.min_segment_rows:
        raise AnalysisError(
            f"Se necesitan al menos {limits.min_segment_rows} filas completas para segmentar (hay {len(data)})."
        )

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler

    cluster_count = 3 if len(data) >= 12 else 2
    values = StandardScaler().fit_transform(data[pair])
    labels = KMeans(n_clusters=cluster_count, n_init=10, random_state=42).fit_predict(
        values
    )
    sample = data if len(data) <= limits.max_segment_rows else data.sample(
        limits.max_segment_rows, random_state=42
    )
    rows = [
        {
            x_column: _json_safe(round(data.at[index, x_column], 4)),
            y_column: _json_safe(round(data.at[index, y_column], 4)),
            "segmento": f"Segmento {labels[index] + 1}",
        }
        for index in sample.index
    ]
    return {
        "rows": rows,
        "columns": _columns_meta(rows, infer_dtype),
        "chart_type": "segment",
        "chart_config": {
            "xKey": x_column,
            "yKey": y_column,
            "segmentKey": "segmento",
        },
        "method": f"KMeans(k={cluster_count}) escalado sobre '{x_column}' y '{y_column}'",
    }


def drivers(tables: dict, question: str, infer_dtype, limits) -> dict:
    frame = _pick_table(
        tables,
        lambda data: len(_numeric_cols(data, _dtypes(data, infer_dtype))) >= 2,
        "Para analizar factores necesito al menos dos columnas numéricas.",
    )
    dtypes = _dtypes(frame, infer_dtype)
    numeric_columns = _numeric_cols(frame, dtypes)
    target = _mentioned_column(question, numeric_columns) or max(
        numeric_columns, key=lambda column: frame[column].var(skipna=True)
    )
    correlation = (
        frame[numeric_columns]
        .corrwith(frame[target], method="spearman")
        .drop(index=target)
        .dropna()
    )
    if correlation.empty:
        raise AnalysisError(
            "No hay columnas con variación suficiente para medir correlaciones."
        )

    top = correlation.reindex(correlation.abs().sort_values(ascending=False).index).head(5)
    rows = [
        {"factor": str(column), "correlacion": _json_safe(round(value, 3))}
        for column, value in top.items()
    ]
    return {
        "rows": rows,
        "columns": _columns_meta(rows, infer_dtype),
        "chart_type": "drivers",
        "chart_config": {"xKey": "correlacion", "yKey": "factor"},
        "method": f"correlación de Spearman contra '{target}'",
    }


def summary(tables: dict, question: str, infer_dtype, limits) -> dict:
    frame = _pick_table(
        tables,
        lambda data: bool(_numeric_cols(data, _dtypes(data, infer_dtype))),
        "Para resumir necesito al menos una columna numérica.",
    )
    dtypes = _dtypes(frame, infer_dtype)
    numeric_columns = _numeric_cols(frame, dtypes)
    rows = []
    for column in numeric_columns:
        series = frame[column].dropna()
        if series.empty:
            continue
        rows.append(
            {
                "columna": str(column),
                "n": int(series.count()),
                "media": _json_safe(round(float(series.mean()), 2)),
                "mediana": _json_safe(round(float(series.median()), 2)),
                "desv_est": _json_safe(round(float(series.std()), 2))
                if len(series) > 1
                else 0,
                "min": _json_safe(series.min()),
                "max": _json_safe(series.max()),
            }
        )
    if not rows:
        raise AnalysisError("Las columnas numéricas no tienen datos para resumir.")
    return {
        "rows": rows,
        "columns": _columns_meta(rows, infer_dtype),
        "chart_type": "table",
        "chart_config": {},
        "method": f"estadísticos descriptivos sobre {len(rows)} columnas numéricas",
    }


_HANDLERS = {
    "forecast": forecast,
    "anomaly": anomaly,
    "segment": segment,
    "drivers": drivers,
    "summary": summary,
}


def run(analysis_type: str, tables: dict, question: str, *, infer_dtype, limits) -> dict:
    """Ejecuta la estrategia estadística con dependencias explícitas."""
    handler = _HANDLERS.get(analysis_type)
    if handler is None:
        raise AnalysisError(f"Tipo de análisis no soportado: {analysis_type}")
    return handler(tables, question, infer_dtype, limits)
