from services.analysis import analysis_service
from services.analysis.analysis_service import AnalysisService


def test_legacy_analysis_service_forwards_arguments_to_application_bridge(monkeypatch):
    captured = {}
    expected = {"success": False, "error_msg": "unsupported"}

    def bridge(analysis_type, dataset_id, question, *, data_source=None):
        captured.update({
            "analysis_type": analysis_type,
            "dataset_id": dataset_id,
            "question": question,
            "data_source": data_source,
        })
        return expected

    monkeypatch.setattr(analysis_service, "execute_legacy_statistical_analysis", bridge)
    source = object()

    result = AnalysisService.execute("summary", 23, "summarize sales", data_source=source)

    assert result is expected
    assert captured == {
        "analysis_type": "summary",
        "dataset_id": 23,
        "question": "summarize sales",
        "data_source": source,
    }
