from sqlalchemy import create_engine, select
from app.database.schema import customers, orders, inspect_schema, format_schema_for_prompt
from app.database.seed import seed_database

def test_seed_creates_expected_tables_and_rows():
    engine = create_engine("sqlite:///:memory:", future=True)
    seed_database(engine)
    schema = inspect_schema(engine)
    assert set(schema) == {"customers", "products", "orders", "order_items"}
    assert "id" in schema["orders"] and "order_date" in schema["orders"]
    with engine.connect() as conn:
        assert len(conn.execute(select(orders)).all()) == 6

def test_schema_formatter():
    text = format_schema_for_prompt({"orders":["id","order_date"]})
    assert "Table orders: id, order_date" in text

def test_seed_is_idempotent():
    engine = create_engine("sqlite:///:memory:", future=True)
    seed_database(engine)
    seed_database(engine)
    with engine.connect() as conn:
        assert len(conn.execute(select(customers)).all()) == 4
        assert len(conn.execute(select(orders)).all()) == 6
