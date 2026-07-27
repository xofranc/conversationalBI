# services/analysis/engine.py
"""
Motor de análisis avanzado. Puro: recibe DataFrames y retorna dicts.
No importa nada de Django — igual que el AI engine.

Cada análisis retorna:
  {
    'rows':         lista de dicts JSON-seguros,
    'columns':      [{'name', 'dtype'}, ...],
    'chart_type':   'forecast' | 'anomaly' | 'segment' | 'drivers',
    'chart_config': claves para que el frontend renderice sin adivinar,
  }

Si los datos no soportan el análisis pedido, lanza AnalysisError con un
mensaje en español para el usuario (se persiste como consulta fallida,
igual que los fallos del LLM — métricas del TFG consistentes).
"""
import re

import pandas as pd
from pandas.tseries.frequencies import to_offset

from apps.dataset.services.schema_service import SchemaService

from . import intent


class AnalysisError(Exception):
    """Error de negocio: los datos no soportan el análisis pedido."""


MAX_HISTORY_PERIODS = 100   # puntos históricos máx. en un pronóstico
MAX_ANOMALIES = 20          # filas máx. en el resultado de anomalías
MAX_SEGMENT_ROWS = 300      # puntos máx. en el scatter de segmentos
FORECAST_HORIZON = 6        # períodos hacia adelante
MIN_FORECAST_PERIODS = 8    # historia mínima para pronosticar


# ── Utilidades compartidas ──────────────────────────────────────────────

def _json_safe(val):
    """Normaliza valores de pandas/numpy a tipos JSON-serializables."""
    if val is None or pd.isna(val):
        return None
    if hasattr(val, 'isoformat'):
        return val.isoformat()
    if hasattr(val, 'item'):
        return val.item()
    return val


def _columns_meta(rows: list) -> list:
    """Infiere {'name', 'dtype'} de las filas resultado (misma heurística del schema)."""
    if not rows:
        return []
    df = pd.DataFrame(rows)
    return [{'name': col, 'dtype': SchemaService.infer_dtype(df[col])} for col in df.columns]


def _dtypes(df: pd.DataFrame) -> dict:
    return {col: SchemaService.infer_dtype(df[col]) for col in df.columns}


def _es_id(df: pd.DataFrame, col) -> bool:
    """Columna identificadora: por nombre (id, id_venta, venta_id) o por
    forma (enteros únicos monótonos, típico autoincremental)."""
    nombre = str(col).lower()
    if nombre == 'id' or nombre.startswith('id_') or nombre.endswith('_id'):
        return True
    serie = df[col]
    return (serie.dtype.kind in 'iu'
            and serie.nunique() == len(serie)
            and serie.is_monotonic_increasing)


def _numeric_cols(df: pd.DataFrame, dtypes: dict) -> list:
    """Numéricas analíticas: sin identificadores (si todo parece ID, se
    devuelven todas — mejor analizar algo que fallar)."""
    cols = [c for c, dt in dtypes.items() if dt in ('int', 'float')]
    sin_ids = [c for c in cols if not _es_id(df, c)]
    return sin_ids or cols


def _pick_table(tables: dict, predicate, error_msg: str) -> pd.DataFrame:
    """Primera tabla (en orden del archivo) que cumple el predicado."""
    for df in tables.values():
        if predicate(df):
            return df
    raise AnalysisError(error_msg)


def _mentioned_column(question: str, candidates: list):
    """Columna candidata mencionada en la pregunta (palabra completa, si hay)."""
    q = question.lower()
    for col in candidates:
        if re.search(rf'\b{re.escape(str(col).lower())}\b', q):
            return col
    return None


# ── Pronóstico ──────────────────────────────────────────────────────────

def forecast(tables: dict, question: str) -> dict:
    """
    Serie temporal: columna fecha + columna numérica → ExponentialSmoothing.
    Retorna la historia seguida de los períodos pronosticados, con banda
    de confianza aproximada (±1.96σ de residuos).
    """
    df = _pick_table(
        tables,
        lambda d: any(dt == 'date' for dt in _dtypes(d).values())
                  and _numeric_cols(d, _dtypes(d)),
        'Para pronosticar necesito una columna de fechas y una numérica en el mismo archivo.',
    )

    dtypes = _dtypes(df)
    date_col = next(c for c, dt in dtypes.items() if dt == 'date')
    num_cols = _numeric_cols(df, dtypes)
    # Por defecto, la medida de mayor variación (suele ser la de negocio)
    y_col = _mentioned_column(question, num_cols) or max(num_cols, key=lambda c: df[c].var(skipna=True))

    serie = (
        df[[date_col, y_col]]
        .assign(**{date_col: pd.to_datetime(df[date_col], format='mixed', errors='coerce')})
        .dropna()
        .groupby(date_col)[y_col].sum()
        .sort_index()
    )
    if len(serie) < 3:
        raise AnalysisError('La columna de fechas tiene muy pocos puntos con datos.')

    # Regulariza la frecuencia a partir del delta mediano entre observaciones
    rule = _freq_rule(serie.index)
    serie = serie.resample(rule).sum()
    if len(serie) > MAX_HISTORY_PERIODS:
        serie = serie.iloc[-MAX_HISTORY_PERIODS:]
    if len(serie) < MIN_FORECAST_PERIODS:
        raise AnalysisError(
            f'Se necesitan al menos {MIN_FORECAST_PERIODS} períodos con datos para pronosticar '
            f'(hay {len(serie)}).'
        )

    from statsmodels.tsa.holtwinters import ExponentialSmoothing
    try:
        fit = ExponentialSmoothing(serie, trend='add', seasonal=None).fit(optimized=True)
    except Exception as e:
        raise AnalysisError(f'No se pudo ajustar el modelo de pronóstico: {e}')

    prediccion = fit.forecast(FORECAST_HORIZON).clip(lower=0)
    sigma = float((serie - fit.fittedvalues).std())

    futuro = pd.date_range(
        serie.index[-1] + to_offset(rule),
        periods=FORECAST_HORIZON, freq=rule,
    )

    rows = [
        {'fecha': idx.date().isoformat(), y_col: _json_safe(round(val, 2)), 'tipo': 'real',
         'inferior': None, 'superior': None}
        for idx, val in serie.items()
    ]
    rows += [
        {
            'fecha': idx.date().isoformat(),
            y_col: _json_safe(round(prediccion.iloc[i], 2)),
            'tipo': 'pronóstico',
            'inferior': _json_safe(round(max(0.0, prediccion.iloc[i] - 1.96 * sigma), 2)),
            'superior': _json_safe(round(prediccion.iloc[i] + 1.96 * sigma, 2)),
        }
        for i, idx in enumerate(futuro)
    ]

    return {
        'rows': rows,
        'columns': _columns_meta(rows),
        'chart_type': intent.FORECAST,
        'chart_config': {'xKey': 'fecha', 'yKey': y_col, 'splitKey': 'tipo'},
        'method': f"ExponentialSmoothing(trend='add') sobre '{y_col}' agrupado por {rule}",
    }


def _freq_rule(index: pd.DatetimeIndex) -> str:
    """Regla de resample a partir del delta mediano entre observaciones."""
    days = pd.Series(index).diff().median().total_seconds() / 86400
    if days <= 1.5:
        return 'D'
    if days <= 9:
        return 'W'
    if days <= 45:
        return 'ME'
    if days <= 100:
        return 'QE'
    return 'YE'


# ── Anomalías ───────────────────────────────────────────────────────────

def anomaly(tables: dict, question: str) -> dict:
    """
    Outliers sobre columnas numéricas: IsolationForest (≥2 columnas) o
    z-score robusto con mediana/MAD (1 columna). Retorna solo las filas
    anómalas, ordenadas por score, con límite duro.
    """
    df = _pick_table(
        tables,
        lambda d: bool(_numeric_cols(d, _dtypes(d))),
        'Para detectar anomalías necesito al menos una columna numérica.',
    )

    dtypes = _dtypes(df)
    num_cols = _numeric_cols(df, dtypes)
    data = df.dropna(subset=num_cols)
    if len(data) < 10:
        raise AnalysisError(f'Se necesitan al menos 10 filas completas para detectar anomalías (hay {len(data)}).')

    if len(num_cols) == 1:
        col = num_cols[0]
        mediana = data[col].median()
        mad = (data[col] - mediana).abs().median() or 1e-9
        z = 0.6745 * (data[col] - mediana).abs() / mad
        mask = z > 3.5
        scores = z[mask]
        metodo = f"z-score robusto (mediana/MAD) sobre '{col}'"
    else:
        from sklearn.ensemble import IsolationForest
        clf = IsolationForest(n_estimators=100, contamination=0.05, random_state=42)
        flags = clf.fit_predict(data[num_cols])
        mask = flags == -1
        scores = -clf.score_samples(data[num_cols])[mask]  # mayor = más anómalo
        metodo = f"IsolationForest sobre {len(num_cols)} columnas numéricas"

    outliers = data[mask].assign(_score=scores).sort_values('_score', ascending=False)
    if outliers.empty:
        raise AnalysisError('No encontré anomalías: los datos son bastante homogéneos.')

    keep = list(df.columns)[:6]
    rows = [
        {**{c: _json_safe(row[c]) for c in keep},
         'score_anomalia': _json_safe(round(row['_score'], 3))}
        for _, row in outliers.head(MAX_ANOMALIES).iterrows()
    ]

    x_key = num_cols[0]
    y_key = num_cols[1] if len(num_cols) > 1 else 'score_anomalia'
    return {
        'rows': rows,
        'columns': _columns_meta(rows),
        'chart_type': intent.ANOMALY,
        'chart_config': {'xKey': x_key, 'yKey': y_key},
        'method': metodo,
    }


# ── Segmentación ────────────────────────────────────────────────────────

def segment(tables: dict, question: str) -> dict:
    """
    KMeans sobre las dos columnas numéricas de mayor varianza (escaladas).
    Retorna los puntos con su etiqueta de segmento para un scatter coloreado.
    """
    df = _pick_table(
        tables,
        lambda d: len(_numeric_cols(d, _dtypes(d))) >= 2,
        'Para segmentar necesito al menos dos columnas numéricas.',
    )

    dtypes = _dtypes(df)
    num_cols = _numeric_cols(df, dtypes)
    par = sorted(num_cols, key=lambda c: df[c].var(skipna=True), reverse=True)[:2]
    x_col, y_col = par
    data = df.dropna(subset=par).reset_index(drop=True)
    if len(data) < 8:
        raise AnalysisError(f'Se necesitan al menos 8 filas completas para segmentar (hay {len(data)}).')

    from sklearn.cluster import KMeans
    from sklearn.preprocessing import StandardScaler
    k = 3 if len(data) >= 12 else 2
    X = StandardScaler().fit_transform(data[par])
    etiquetas = KMeans(n_clusters=k, n_init=10, random_state=42).fit_predict(X)

    muestra = data if len(data) <= MAX_SEGMENT_ROWS else data.sample(MAX_SEGMENT_ROWS, random_state=42)
    rows = [
        {
            x_col: _json_safe(round(data.at[i, x_col], 4)),
            y_col: _json_safe(round(data.at[i, y_col], 4)),
            'segmento': f'Segmento {etiquetas[i] + 1}',
        }
        for i in muestra.index
    ]

    return {
        'rows': rows,
        'columns': _columns_meta(rows),
        'chart_type': intent.SEGMENT,
        'chart_config': {'xKey': x_col, 'yKey': y_col, 'segmentKey': 'segmento'},
        'method': f"KMeans(k={k}) escalado sobre '{x_col}' y '{y_col}'",
    }


# ── Factores (drivers) ──────────────────────────────────────────────────

def drivers(tables: dict, question: str) -> dict:
    """
    Qué mueve a una variable: correlación de Spearman de cada numérica
    contra el objetivo (mencionado en la pregunta o el de mayor varianza).
    Retorna los 5 factores más fuertes, con signo.
    """
    df = _pick_table(
        tables,
        lambda d: len(_numeric_cols(d, _dtypes(d))) >= 2,
        'Para analizar factores necesito al menos dos columnas numéricas.',
    )

    dtypes = _dtypes(df)
    num_cols = _numeric_cols(df, dtypes)
    target = _mentioned_column(question, num_cols) or max(num_cols, key=lambda c: df[c].var(skipna=True))

    corr = df[num_cols].corrwith(df[target], method='spearman').drop(index=target).dropna()
    if corr.empty:
        raise AnalysisError('No hay columnas con variación suficiente para medir correlaciones.')

    top = corr.reindex(corr.abs().sort_values(ascending=False).index).head(5)
    rows = [
        {'factor': str(col), 'correlacion': _json_safe(round(val, 3))}
        for col, val in top.items()
    ]

    return {
        'rows': rows,
        'columns': _columns_meta(rows),
        'chart_type': intent.DRIVERS,
        'chart_config': {'xKey': 'correlacion', 'yKey': 'factor'},
        'method': f"correlación de Spearman contra '{target}'",
    }


# ── Dispatcher ──────────────────────────────────────────────────────────

_HANDLERS = {
    intent.FORECAST: forecast,
    intent.ANOMALY: anomaly,
    intent.SEGMENT: segment,
    intent.DRIVERS: drivers,
}


def run(analysis_type: str, tables: dict, question: str) -> dict:
    handler = _HANDLERS.get(analysis_type)
    if handler is None:
        raise AnalysisError(f'Tipo de análisis no soportado: {analysis_type}')
    return handler(tables, question)
