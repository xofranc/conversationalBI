class PromptBuilder:

    TEMPLATE = """\
Eres un experto en SQL. Convierte la pregunta en español a una consulta SQL válida.

ESQUEMA:
{schema_text}

REGLAS:
- Responde ÚNICAMENTE con el SQL, sin explicaciones ni bloques markdown.
- Solo puedes usar SELECT. Nunca uses INSERT, UPDATE, DELETE, DROP, ALTER.
- Usa los nombres de tablas y columnas exactamente como aparecen en el esquema.
- Si la pregunta no se puede responder con el esquema dado, responde exactamente: NO_SQL_POSSIBLE

PREGUNTA: {question}

SQL:"""

    CORRECTION_TEMPLATE = """\
El SQL que generaste produjo un error. Corrígelo.

SQL ANTERIOR:
{previous_sql}

ERROR:
{error}

ESQUEMA:
{schema_text}

Responde ÚNICAMENTE con el SQL corregido:

SQL:"""

    @classmethod
    def build(cls, question: str, schema: dict) -> str:
        return cls.TEMPLATE.format(
            schema_text = cls._schema_to_text(schema),
            question    = question,
        )

    @classmethod
    def build_correction(cls, question: str, schema: dict,
                         previous_sql: str, error: str) -> str:
        return cls.CORRECTION_TEMPLATE.format(
            schema_text  = cls._schema_to_text(schema),
            previous_sql = previous_sql,
            error        = error,
        )

    @staticmethod
    def _schema_to_text(schema: dict) -> str:
        lines = []
        for table in schema.get('tables', []):
            cols = ', '.join(
                f"{c['name']} ({c['dtype']})"
                for c in table.get('columns', [])
            )
            sample_vals = []
            for c in table.get('columns', []):
                if c.get('sample'):
                    sample_vals.append(f"{c['name']}: {c['sample'][:2]}")

            lines.append(f"Tabla: {table['name']}")
            lines.append(f"  Columnas: {cols}")
            if sample_vals:
                lines.append(f"  Ejemplos: {', '.join(sample_vals)}")
        return '\n'.join(lines)