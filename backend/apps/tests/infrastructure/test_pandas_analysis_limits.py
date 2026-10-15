import pytest

pd = pytest.importorskip("pandas")

from apps.queries.domain.policies import AnalysisLimits
from apps.queries.infrastructure.analysis import engine


def infer_dtype(series):
    return "float" if pd.api.types.is_numeric_dtype(series) else "str"


def test_pandas_anomaly_engine_uses_injected_minimum_row_boundary():
    frame = pd.DataFrame({"amount": [1.0] * 7 + [100.0]})

    with pytest.raises(engine.AnalysisError, match="10 filas"):
        engine.anomaly({"sales": frame}, "find anomalies", infer_dtype, AnalysisLimits())

    result = engine.anomaly(
        {"sales": frame},
        "find anomalies",
        infer_dtype,
        AnalysisLimits(min_anomaly_rows=8),
    )
    assert len(result["rows"]) == 1
    assert result["rows"][0]["amount"] == 100.0


def test_pandas_segment_engine_uses_injected_minimum_row_boundary():
    pytest.importorskip("sklearn")
    frame = pd.DataFrame({
        "x": [0.0, 0.2, 0.1, 10.0, 10.2, 10.1, 5.0],
        "y": [0.1, 0.0, 0.2, 10.1, 10.0, 10.2, 5.1],
    })

    with pytest.raises(engine.AnalysisError, match="8 filas"):
        engine.segment({"sales": frame}, "segment data", infer_dtype, AnalysisLimits())

    result = engine.segment(
        {"sales": frame},
        "segment data",
        infer_dtype,
        AnalysisLimits(min_segment_rows=7),
    )
    assert len(result["rows"]) == 7
