"""Preguntas sugeridas de forma determinista a partir del esquema."""


def suggest(schema: dict, limit: int = 3) -> list[str]:
    tables = schema.get("tables", [])
    if not tables:
        return []
    table = tables[0]
    name = table.get("name", "main")
    columns = table.get("columns", [])

    def first(*dtypes):
        for column in columns:
            if column.get("dtype") in dtypes:
                return column["name"]
        return None

    date = first("date")
    numeric = first("float", "int")
    categorical = first("str")
    suggestions = []
    if categorical and numeric:
        suggestions.append(f"{numeric} total por {categorical}".replace("_", " "))
    if date and numeric:
        suggestions.append(f"evolución mensual de {numeric}".replace("_", " "))
    if categorical:
        suggestions.append(f"top 5 {categorical} en {name}".replace("_", " "))
    if numeric:
        suggestions.append("dame un resumen de los datos")
    return suggestions[:limit]
