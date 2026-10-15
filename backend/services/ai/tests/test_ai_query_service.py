from apps.queries.application.dtos import EngineResultDTO
from services.ai.ai_query_service import AIQueryService


def test_legacy_ai_service_bridges_application_dtos_to_legacy_response(monkeypatch):
    captured = {}

    class EngineFake:
        def execute(self, request):
            captured["request"] = request
            return EngineResultDTO(
                sql="SELECT 1",
                success=True,
                retry_count=2,
                rows=({"value": 1},),
                columns=({"name": "value", "dtype": "int"},),
                chart_type="bar",
                chart_config={"xKey": "value"},
                answer="one",
            )

    import apps.queries.infrastructure.composition as composition
    monkeypatch.setattr(composition, "build_ai_query_engine", lambda *, data_source: EngineFake())

    result = AIQueryService.execute(
        "show value", 4, {"tables": []},
        history=[{"question": "previous", "sql": "SELECT 0"}],
        data_source=object(),
    )

    request = captured["request"]
    assert (request.question, request.dataset_id, request.schema) == (
        "show value", 4, {"tables": []},
    )
    assert [(turn.question, turn.sql) for turn in request.history] == [
        ("previous", "SELECT 0"),
    ]
    assert result["success"] is True
    assert result["retry_count"] == 2 and result["rows"] == [{"value": 1}]
    assert result["chart_config"] == {"xKey": "value"}
    assert result["suggestions"] == []
