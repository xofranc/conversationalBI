"""Legacy compatibility shim for the queries AI chart selector."""

from apps.queries.infrastructure.ai.chart_selector import ChartSelector as _ChartSelector


class ChartSelector(_ChartSelector):
    """Preserve the old ``pick`` convenience method while delegating selection."""

    @staticmethod
    def pick(columns: list, rows: list) -> str:
        return _ChartSelector.select(columns, rows)["chart_type"]


__all__ = ["ChartSelector"]
