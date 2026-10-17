"""Prompts técnicos usados por la generación SQL y la narrativa AI."""


class PromptBuilder:
    TEMPLATE = """\
Eres un analista de datos experto en SQLite. Convierte la pregunta del usuario a UNA consulta SQL válida para SQLite.

ESQUEMA DE LA BASE DE DATOS:
{schema_text}
{history_text}
REGLAS:
- Responde ÚNICAMENTE con el SQL: sin explicaciones, sin markdown, sin comentarios.
- Solo SELECT. Nunca INSERT, UPDATE, DELETE, DROP, ALTER, PRAGMA ni ATTACH.
- Usa los nombres de tablas y columnas exactamente como aparecen en el esquema; si contienen espacios o tildes, enciérralos entre comillas dobles.
- Las fechas están almacenadas como texto ISO ('YYYY-MM-DD'): usa strftime('%Y', col), strftime('%Y-%m', col) o date(col) para agrupar por períodos.
- Para filtros de texto usa LOWER(col) LIKE '%valor%'; fíjate en los valores reales de cada columna (tildes y mayúsculas exactas).
- Pon un alias descriptivo a cada columna calculada (AS total_ventas).
- Para rankings o "top N": ORDER BY ... DESC LIMIT N.
- Si la pregunta pide listar filas sin agregar y no pide todo, agrega LIMIT 100.
- Si hay varias tablas, relaciónalas con JOIN por las columnas comunes.
- Si la pregunta es de seguimiento ("y por mes?", "ahora por ciudad"), retoma el tema de la CONVERSACIÓN PREVIA.
- Los EJEMPLOS son ilustrativos: usa solo las tablas y columnas del ESQUEMA.
- Si la pregunta no se puede responder con el esquema dado, responde exactamente: NO_SQL_POSSIBLE

EJEMPLOS:
Pregunta: ventas totales por ciudad
SQL: SELECT ciudad, SUM(monto) AS ventas_totales FROM ventas GROUP BY ciudad ORDER BY ventas_totales DESC

Pregunta: evolución mensual de ingresos
SQL: SELECT strftime('%Y-%m', fecha) AS mes, SUM(ingreso) AS ingresos FROM ventas GROUP BY mes ORDER BY mes

Pregunta: top 5 productos por unidades
SQL: SELECT producto, SUM(cantidad) AS unidades FROM ventas GROUP BY producto ORDER BY unidades DESC LIMIT 5

PREGUNTA: {question}

SQL:"""

    CORRECTION_TEMPLATE = """\
El SQL que generaste para SQLite produjo un error. Corrígelo.

PREGUNTA ORIGINAL: {question}

SQL ANTERIOR:
{previous_sql}

ERROR:
{error}

ESQUEMA DE LA BASE DE DATOS:
{schema_text}

REGLAS:
- Responde ÚNICAMENTE con el SQL corregido: sin explicaciones ni markdown.
- Solo SELECT. Usa los nombres exactos del esquema.
- Recuerda: fechas como texto ISO (usa strftime/date), filtros de texto con LOWER(col) LIKE y los valores reales de la columna.
- Si la pregunta no se puede responder con el esquema dado, responde exactamente: NO_SQL_POSSIBLE

SQL:"""

    EMPTY_RESULT_TEMPLATE = """\
El SQL que generaste es válido pero devolvió 0 filas. Revisa los filtros.

PREGUNTA ORIGINAL: {question}

SQL ANTERIOR:
{previous_sql}

ESQUEMA DE LA BASE DE DATOS (fíjate en los valores reales de cada columna):
{schema_text}

PISTAS:
- Compara los valores de tus filtros con los valores reales listados en el esquema: mayúsculas, tildes y formato exacto.
- Prefiere LOWER(col) LIKE '%valor%' sobre igualdades exactas en columnas de texto.
- Verifica rangos de fechas contra el rango real de la columna.

Responde ÚNICAMENTE con el SQL corregido:

SQL:"""

    ANSWER_TEMPLATE = """\
Eres un analista de datos que conversa en español. Redacta la respuesta a la pregunta del usuario usando los resultados de la consulta.

PREGUNTA: {question}

CONSULTA EJECUTADA:
{sql}

RESULTADOS ({row_count} filas):
{rows_text}

INSTRUCCIONES:
- Responde de forma directa y completa en 2 a 4 frases, en español, sin markdown.
- Menciona las cifras concretas más relevantes (totales, máximos, mínimos, primeros del ranking).
- Redondea los números grandes (ej: 215.8 millones) y usa formato de moneda si la columna lo sugiere.
- No repitas la pregunta ni hables del SQL ni de la base de datos.
- Si solo hay una fila con una cifra, dilo en una frase directa.

RESPUESTA:"""

    MAX_ANSWER_ROWS = 15

    @classmethod
    def build(cls, question: str, schema: dict, history: list | None = None) -> str:
        return cls.TEMPLATE.format(
            schema_text=cls._schema_to_text(schema),
            question=question,
            history_text=cls._history_to_text(history),
        )

    @classmethod
    def build_correction(cls, question: str, schema: dict, previous_sql: str, error: str) -> str:
        return cls.CORRECTION_TEMPLATE.format(
            question=question,
            schema_text=cls._schema_to_text(schema),
            previous_sql=previous_sql,
            error=error,
        )

    @classmethod
    def build_empty_result(cls, question: str, schema: dict, previous_sql: str) -> str:
        return cls.EMPTY_RESULT_TEMPLATE.format(
            question=question,
            schema_text=cls._schema_to_text(schema),
            previous_sql=previous_sql,
        )

    @classmethod
    def build_answer(cls, question: str, sql: str, rows: list, row_count: int) -> str:
        return cls.ANSWER_TEMPLATE.format(
            question=question,
            sql=sql,
            rows_text=cls._rows_to_text(rows),
            row_count=row_count,
        )

    @classmethod
    def _rows_to_text(cls, rows: list) -> str:
        lines = [" | ".join(f"{key}: {value}" for key, value in row.items()) for row in rows[:cls.MAX_ANSWER_ROWS]]
        if len(rows) > cls.MAX_ANSWER_ROWS:
            lines.append(f"… y {len(rows) - cls.MAX_ANSWER_ROWS} filas más")
        return "\n".join(lines) if lines else "(sin filas)"

    @staticmethod
    def _history_to_text(history: list | None) -> str:
        if not history:
            return ""
        lines = ["CONVERSACIÓN PREVIA (tema de la charla, para preguntas de seguimiento):"]
        for item in history:
            lines.append(f"- Pregunta: {item['question']}")
            lines.append(f"  SQL: {item['sql']}")
        return "\n".join(lines) + "\n"

    @staticmethod
    def _schema_to_text(schema: dict) -> str:
        lines = []
        for table in schema.get("tables", []):
            columns = ", ".join(f"{column['name']} ({column['dtype']})" for column in table.get("columns", []))
            header = f"Tabla: {table['name']}"
            if table.get("row_count") is not None:
                header += f"  ({table['row_count']} filas)"
            lines.extend((header, f"  Columnas: {columns}"))
            values = []
            for column in table.get("columns", []):
                if column.get("info"):
                    values.append(f"{column['name']} → {column['info']}")
                elif column.get("sample"):
                    values.append(f"{column['name']}: {column['sample'][:3]}")
            if values:
                lines.append(f"  Valores: {'; '.join(values)}")
        return "\n".join(lines)
