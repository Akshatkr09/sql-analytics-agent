"""Prompt construction for natural-language-to-SQL generation."""

SQL_GENERATION_INSTRUCTIONS = """You are a careful SQL analyst.
Convert the user's natural-language question into exactly one SQLite SELECT query.

Rules:
- Generate read-only SELECT statements only.
- Never generate INSERT, UPDATE, DELETE, DROP, ALTER, CREATE, REPLACE, PRAGMA,
  ATTACH, DETACH, or any other write or administrative statement.
- Use only tables and columns present in the supplied database schema.
- Do not invent table names or column names.
- Prefer explicit column names over SELECT * when practical.
- Use SQLite-compatible SQL syntax.
- Do not include explanations, Markdown fences, or comments.
- Return only the SQL statement.
"""


def build_sql_prompt(user_query: str, schema_text: str, previous_sql: str | None = None,
                     error_message: str | None = None) -> str:
    """Build the SQL generation prompt, optionally including correction context."""
    prompt = (
        f"{SQL_GENERATION_INSTRUCTIONS}\n"
        f"Database schema:\n{schema_text}\n\n"
        f"User question:\n{user_query.strip()}\n"
    )
    if previous_sql and error_message:
        prompt += (
            "\nThe previous SQL failed. Correct it using the database error below.\n"
            f"Previous SQL:\n{previous_sql}\n"
            f"Database error:\n{error_message}\n"
            "Return a corrected SELECT query only.\n"
        )
    return prompt
