from types import SimpleNamespace

from services.analysis.analysis_service import AnalysisService


def test_legacy_analysis_service_maps_application_result_without_database():
    schema = {"tables": [{"name": "sales"}]}
    captured = {}

    class EngineFake:
        def execute(self, request):
            captured["request"] = request
            return SimpleNamespace(
                sql="SELECT amount FROM sales",
                success=True,
                error_message="",
                retry_count=1,
                execution_time=0.25,
                rows=({"amount": 42},),
                columns=({"name": "amount", "dtype": "integer"},),
                chart_type="bar",
                chart_config={"x": "month"},
                answer="Total: 42",
                suggestions=("Compare months",),
            )

    result = AnalysisService.execute(
        "summary",
        23,
        "summarize sales",
        analysis_engine=EngineFake(),
        schema=schema,
    )

    assert result == {
        "sql": "SELECT amount FROM sales",
        "model_used": "análisis:resumen",
        "success": True,
        "error_msg": "",
        "retry_count": 1,
        "execution_time": 0.25,
        "rows": [{"amount": 42}],
        "columns": [{"name": "amount", "dtype": "integer"}],
        "chart_type": "bar",
        "chart_config": {"x": "month"},
        "answer": "Total: 42",
        "suggestions": ["Compare months"],
    }
    request = captured["request"]
    assert (request.intent, request.dataset_id, request.question, request.schema) == (
        "summary",
        23,
        "summarize sales",
        schema,
    )
