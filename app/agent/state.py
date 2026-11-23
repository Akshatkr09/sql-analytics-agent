"""Typed state shared by the LangGraph SQL workflow."""
from typing import Any, TypedDict


class SQLAgentState(TypedDict, total=False):
    user_query: str
    generated_sql: str
    db_result: list[dict[str, Any]]
    error_message: str | None
    retry_count: int
    schema_text: str
    status: str
    correction_logs: list[str]
