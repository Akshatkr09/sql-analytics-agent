"""Generate SQL from natural-language questions using Gemini."""
import re

from app.agent.prompts import build_sql_prompt
from app.llm.gemini_client import get_gemini_client, get_gemini_model


def clean_sql_response(response_text: str) -> str:
    """Remove optional Markdown fences and normalize Gemini's SQL response."""
    if not response_text or not response_text.strip():
        raise ValueError("Gemini returned an empty SQL response.")

    text = response_text.strip()
    fenced = re.fullmatch(r"```(?:sql)?\s*(.*?)\s*```", text, flags=re.IGNORECASE | re.DOTALL)
    if fenced:
        text = fenced.group(1).strip()

    if not text:
        raise ValueError("Gemini returned an empty SQL response.")
    return text.rstrip(";").strip() + ";"


def generate_sql(user_query: str, schema_text: str, *,
                 previous_sql: str | None = None,
                 error_message: str | None = None,
                 client=None, model: str | None = None) -> str:
    """Ask Gemini to produce a single SQLite SELECT query.

    `client` and `model` are injectable so unit tests do not require an API call.
    """
    if not user_query or not user_query.strip():
        raise ValueError("User question cannot be empty.")
    if not schema_text or not schema_text.strip():
        raise ValueError("Database schema is required for SQL generation.")

    active_client = client or get_gemini_client()
    active_model = model or get_gemini_model()
    prompt = build_sql_prompt(
        user_query, schema_text, previous_sql=previous_sql, error_message=error_message
    )
    response = active_client.models.generate_content(
        model=active_model,
        contents=prompt,
    )
    response_text = getattr(response, "text", None)
    return clean_sql_response(response_text or "")
