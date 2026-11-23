from types import SimpleNamespace

import pytest

from app.agent.sql_generator import clean_sql_response, generate_sql

SCHEMA = "Table orders: id, order_date, total_amount"


class FakeModels:
    def __init__(self, text):
        self.text = text
        self.last_call = None

    def generate_content(self, **kwargs):
        self.last_call = kwargs
        return SimpleNamespace(text=self.text)


class FakeClient:
    def __init__(self, text):
        self.models = FakeModels(text)


def test_clean_sql_response_removes_markdown_fence():
    assert clean_sql_response("```sql\nSELECT id FROM orders\n```") == "SELECT id FROM orders;"


def test_generate_sql_uses_injected_client_and_schema():
    client = FakeClient("SELECT id, order_date FROM orders ORDER BY order_date")
    result = generate_sql("Show orders sorted by date", SCHEMA, client=client, model="test-model")

    assert result == "SELECT id, order_date FROM orders ORDER BY order_date;"
    assert client.models.last_call["model"] == "test-model"
    assert "order_date" in client.models.last_call["contents"]
    assert "Show orders sorted by date" in client.models.last_call["contents"]


def test_generate_sql_includes_error_context_for_correction():
    client = FakeClient("SELECT id FROM orders ORDER BY order_date")
    generate_sql(
        "Show orders sorted by date",
        SCHEMA,
        previous_sql="SELECT * FROM orders ORDER BY created_at",
        error_message="no such column: created_at",
        client=client,
    )
    prompt = client.models.last_call["contents"]
    assert "no such column: created_at" in prompt
    assert "created_at" in prompt
    assert "order_date" in prompt


def test_generate_sql_rejects_empty_question():
    with pytest.raises(ValueError, match="question cannot be empty"):
        generate_sql(" ", SCHEMA, client=FakeClient("SELECT 1"))


def test_generate_sql_rejects_empty_schema():
    with pytest.raises(ValueError, match="schema is required"):
        generate_sql("Show orders", " ", client=FakeClient("SELECT 1"))


def test_generate_sql_rejects_empty_model_response():
    with pytest.raises(ValueError, match="empty SQL response"):
        generate_sql("Show orders", SCHEMA, client=FakeClient(" "))
