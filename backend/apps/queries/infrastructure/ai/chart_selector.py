"""Selección determinista de visualización para resultados SQL."""


class ChartSelector:
    @staticmethod
    def select(columns: list, rows: list) -> dict:
        empty = {"chart_type": "table", "chart_config": {}}
        if not rows or not columns:
            return empty
        numeric = [column["name"] for column in columns if column["dtype"] in ("int", "float")]
        categorical = [column["name"] for column in columns if column["dtype"] == "str"]
        dates = [column["name"] for column in columns if column["dtype"] == "date"]
        if dates and numeric:
            return {"chart_type": "line", "chart_config": {"xKey": dates[0], "yKey": numeric[0]}}
        if categorical and numeric:
            chart_type = "pie" if len(categorical) == len(numeric) == 1 and 1 < len(rows) <= 6 else "bar"
            return {
                "chart_type": chart_type,
                "chart_config": {
                    "xKey": categorical[0],
                    "yKey": numeric[0],
                    "nameKey": categorical[0],
                    "valueKey": numeric[0],
                },
            }
        if len(numeric) == 2 and not categorical:
            return {"chart_type": "scatter", "chart_config": {"xKey": numeric[0], "yKey": numeric[1]}}
        return empty
