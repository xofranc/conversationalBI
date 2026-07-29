def suggest(schema: dict, limit: int = 3) -> list:
    """
    Preguntas de ejemplo construidas desde el esquema, para cuando una
    consulta falla: la conversación no muere, ofrece caminos.
    Determinista (sin LLM) y en español.
    """
    tables = schema.get('tables', [])
    if not tables:
        return []

    table = tables[0]
    name = table.get('name', 'main')
    cols = table.get('columns', [])

    def _first(*dtypes):
        for c in cols:
            if c.get('dtype') in dtypes:
                return c['name']
        return None

    fecha = _first('date')
    numerica = _first('float', 'int')
    categorica = _first('str')

    sugerencias = []
    if categorica and numerica:
        sugerencias.append(f'{numerica} total por {categorica}'.replace('_', ' '))
    if fecha and numerica:
        sugerencias.append(f'evolución mensual de {numerica}'.replace('_', ' '))
    if categorica:
        sugerencias.append(f'top 5 {categorica} en {name}'.replace('_', ' '))
    if numerica:
        sugerencias.append('dame un resumen de los datos')

    return sugerencias[:limit]
