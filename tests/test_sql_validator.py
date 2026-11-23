import pytest

from app.security.sql_validator import validate_read_only_sql


@pytest.mark.parametrize("sql", [
    "SELECT * FROM orders",
    "WITH recent AS (SELECT * FROM orders) SELECT * FROM recent",
])
def test_allows_read_only_select(sql):
    assert validate_read_only_sql(sql).allowed


@pytest.mark.parametrize("sql", [
    "INSERT INTO orders(id) VALUES (9)",
    "UPDATE orders SET status='x'",
    "DELETE FROM orders",
    "DROP TABLE orders",
    "ALTER TABLE orders ADD COLUMN x TEXT",
    "SELECT * FROM orders; DROP TABLE orders",
    "SELECT * INTO backup FROM orders",
    "not valid sql",
    "",
])
def test_rejects_write_or_invalid_sql(sql):
    assert not validate_read_only_sql(sql).allowed
