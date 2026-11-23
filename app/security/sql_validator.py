"""Read-only SQL validation using SQLGlot's parsed AST (not string matching)."""
from dataclasses import dataclass

from sqlglot import exp, parse
from sqlglot.errors import ParseError


@dataclass(frozen=True)
class SQLValidationResult:
    allowed: bool
    reason: str


def validate_read_only_sql(sql: str) -> SQLValidationResult:
    """Allow exactly one read-only SELECT statement for the SQLite backend."""
    if not isinstance(sql, str) or not sql.strip():
        return SQLValidationResult(False, "SQL query is empty.")

    try:
        statements = [statement for statement in parse(sql, read="sqlite") if statement]
    except ParseError as exc:
        return SQLValidationResult(False, f"SQL could not be parsed: {exc}")
    except Exception as exc:
        return SQLValidationResult(False, f"SQL validation failed: {exc}")

    if len(statements) != 1:
        return SQLValidationResult(False, "Only one SQL statement is permitted.")

    statement = statements[0]
    if not isinstance(statement, exp.Query):
        return SQLValidationResult(False, "Only read-only SELECT queries are permitted.")
    if isinstance(statement, (exp.Insert, exp.Update, exp.Delete, exp.Drop, exp.Alter, exp.Create)):
        return SQLValidationResult(False, "Write and schema-changing statements are blocked.")

    # SELECT INTO can create a table in some SQL dialects; do not permit it.
    if statement.find(exp.Into):
        return SQLValidationResult(False, "SELECT INTO is not permitted.")

    return SQLValidationResult(True, "Read-only SQL accepted.")
