class ChartSelector:

    @staticmethod
    def pick(columns: list, rows: list) -> str:
        if not rows or not columns:
            return 'table'

        num_cols  = [c for c in columns if c['dtype'] in ('int', 'float')]
        cat_cols  = [c for c in columns if c['dtype'] == 'str']
        date_cols = [c for c in columns if c['dtype'] == 'date']
        num_rows  = len(rows)

        if date_cols and num_cols:
            return 'line'

        if len(cat_cols) == 1 and len(num_cols) == 1:
            return 'pie' if num_rows <= 6 else 'bar'

        if len(num_cols) == 2 and not cat_cols:
            return 'scatter'

        return 'table'