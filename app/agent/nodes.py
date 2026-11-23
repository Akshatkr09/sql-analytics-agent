"""LangGraph nodes with SQL AST enforcement and explicit self-correction."""
from sqlalchemy import text

from app.agent.sql_generator import generate_sql
from app.database.connection import get_engine
from app.database.schema import format_schema_for_prompt, inspect_schema
from app.security.sql_validator import validate_read_only_sql


def inspect_schema_node(state: dict) -> dict:
    schema = inspect_schema(get_engine())
    return {"schema_text": format_schema_for_prompt(schema), "error_message": None}


def generate_sql_node(state: dict) -> dict:
    sql = generate_sql(
        state["user_query"], state["schema_text"],
        previous_sql=state.get("generated_sql"),
        error_message=state.get("error_message"),
    )
    return {"generated_sql": sql, "error_message": None, "status": "generated"}


def execute_query_node(state: dict) -> dict:
    """Validate generated SQL's AST before executing it against SQLite."""
    sql = state.get("generated_sql", "")
    validation = validate_read_only_sql(sql)
    if not validation.allowed:
        return {"db_result": [], "error_message": validation.reason, "status": "blocked"}
    try:
        with get_engine().connect() as connection:
            result = connection.execute(text(sql))
            rows = [dict(row._mapping) for row in result.fetchall()]
        return {"db_result": rows, "error_message": None, "status": "success"}
    except Exception as exc:
        return {"db_result": [], "error_message": str(exc), "status": "error"}


def reflection_node(state: dict) -> dict:
    """Record the failure and increment the retry counter."""
    retry_count = state.get("retry_count", 0) + 1
    logs = list(state.get("correction_logs", []))
    logs.append(f"Retry {retry_count}: {state.get('error_message', 'Unknown database error')}")
    return {"retry_count": retry_count, "correction_logs": logs}
