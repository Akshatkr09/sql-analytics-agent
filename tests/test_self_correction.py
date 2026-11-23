"""Deterministic tests for the graph's SQL correction loop."""
from datetime import date
from sqlalchemy import create_engine

from app.agent import nodes as nodes_module
from app.agent.graph import build_sql_agent
from app.database.schema import metadata, customers, orders


def make_test_database():
    engine = create_engine("sqlite:///:memory:", future=True)
    metadata.create_all(engine)
    with engine.begin() as conn:
        conn.execute(customers.insert(), [
            {"customer_id": 1, "name": "Test Customer", "city": "Patna", "email": "test@example.com"}
        ])
        conn.execute(orders.insert(), [
            {"id": 1, "customer_id": 1, "order_date": date(2026, 1, 12),
             "total_amount": 100.0, "status": "Delivered"}
        ])
    return engine


def test_graph_corrects_invalid_column_and_returns_rows(monkeypatch):
    engine = make_test_database()
    # The graph nodes import get_engine from the database connection module.
    # Patch the name where the nodes look it up.
    monkeypatch.setattr(nodes_module, "get_engine", lambda: engine)

    generated = iter([
        "SELECT id, created_at FROM orders ORDER BY created_at;",
        "SELECT id, order_date FROM orders ORDER BY order_date;",
    ])
    prompts = []

    def fake_generate_sql(user_query, schema_text, **kwargs):
        prompts.append(kwargs)
        return next(generated)

    monkeypatch.setattr(nodes_module, "generate_sql", fake_generate_sql)

    result = build_sql_agent().invoke({
        "user_query": "Show orders sorted by date",
        "generated_sql": "",
        "db_result": [],
        "error_message": None,
        "retry_count": 0,
        "schema_text": "",
        "status": "started",
        "correction_logs": [],
    })

    assert result["status"] == "success"
    assert result["retry_count"] == 1
    assert result["db_result"][0]["order_date"] == "2026-01-12"
    assert "order_date" in result["generated_sql"]
    assert len(result["correction_logs"]) == 1
    assert "no such column" in result["correction_logs"][0].lower()
    assert "created_at" in prompts[1]["previous_sql"]
    assert "no such column" in prompts[1]["error_message"].lower()


def test_graph_stops_after_three_failed_retries(monkeypatch):
    engine = create_engine("sqlite:///:memory:", future=True)
    metadata.create_all(engine)
    monkeypatch.setattr(nodes_module, "get_engine", lambda: engine)
    monkeypatch.setattr(
        nodes_module,
        "generate_sql",
        lambda *args, **kwargs: "SELECT missing_column FROM orders;",
    )

    result = build_sql_agent().invoke({
        "user_query": "Show orders",
        "generated_sql": "",
        "db_result": [],
        "error_message": None,
        "retry_count": 0,
        "schema_text": "",
        "status": "started",
        "correction_logs": [],
    })

    assert result["status"] == "error"
    assert result["retry_count"] == 3
    assert len(result["correction_logs"]) == 3
