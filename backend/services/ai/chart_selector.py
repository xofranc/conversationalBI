class ChartSelector:

    @staticmethod
    def pick(columns: list, rows: list) -> str:
        """Compatibilidad: solo el tipo de gráfico."""
        return ChartSelector.select(columns, rows)['chart_type']

    @staticmethod
    def select(columns: list, rows: list) -> dict:
        """
        Retorna {'chart_type', 'chart_config'} con las claves listas para
        que el frontend renderice sin adivinar (xKey/yKey/nameKey/valueKey),
        igual que el contrato del motor de análisis.
        """
        empty = {'chart_type': 'table', 'chart_config': {}}
        if not rows or not columns:
            return empty

        num_cols  = [c['name'] for c in columns if c['dtype'] in ('int', 'float')]
        cat_cols  = [c['name'] for c in columns if c['dtype'] == 'str']
        date_cols = [c['name'] for c in columns if c['dtype'] == 'date']
        num_rows  = len(rows)

        # Serie temporal: fecha + medida → línea
        if date_cols and num_cols:
            return {
                'chart_type': 'line',
                'chart_config': {'xKey': date_cols[0], 'yKey': num_cols[0]},
            }

        # Categoría + medida → torta (pocas categorías) o barras
        if len(cat_cols) >= 1 and len(num_cols) >= 1:
            chart_type = 'pie' if (len(cat_cols) == 1 and len(num_cols) == 1
                                   and 1 < num_rows <= 6) else 'bar'
            return {
                'chart_type': chart_type,
                'chart_config': {
                    'xKey': cat_cols[0], 'yKey': num_cols[0],
                    'nameKey': cat_cols[0], 'valueKey': num_cols[0],
                },
            }

        # Dos medidas sin categorías → dispersión
        if len(num_cols) == 2 and not cat_cols:
            return {
                'chart_type': 'scatter',
                'chart_config': {'xKey': num_cols[0], 'yKey': num_cols[1]},
            }

        return empty
