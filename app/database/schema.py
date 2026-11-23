"""Sample analytics schema and SQLAlchemy reflection helpers."""
from sqlalchemy import Column, Date, Float, ForeignKey, Integer, MetaData, String, Table, inspect

metadata = MetaData()
customers = Table("customers", metadata,
    Column("customer_id", Integer, primary_key=True),
    Column("name", String(120), nullable=False),
    Column("city", String(80)),
    Column("email", String(160), unique=True))
products = Table("products", metadata,
    Column("product_id", Integer, primary_key=True),
    Column("product_name", String(120), nullable=False),
    Column("category", String(80)),
    Column("price", Float, nullable=False))
orders = Table("orders", metadata,
    Column("id", Integer, primary_key=True),
    Column("customer_id", Integer, ForeignKey("customers.customer_id")),
    Column("order_date", Date, nullable=False),
    Column("total_amount", Float, nullable=False),
    Column("status", String(40), nullable=False))
order_items = Table("order_items", metadata,
    Column("item_id", Integer, primary_key=True),
    Column("order_id", Integer, ForeignKey("orders.id"), nullable=False),
    Column("product_id", Integer, ForeignKey("products.product_id"), nullable=False),
    Column("quantity", Integer, nullable=False),
    Column("unit_price", Float, nullable=False))

def inspect_schema(engine) -> dict[str, list[str]]:
    """Read actual table and column metadata from the connected database."""
    inspector = inspect(engine)
    return {name: [col["name"] for col in inspector.get_columns(name)]
            for name in inspector.get_table_names()}

def format_schema_for_prompt(schema: dict[str, list[str]]) -> str:
    if not schema:
        return "No tables are available in the database."
    return "\n".join(f"Table {name}: {', '.join(cols)}"
                     for name, cols in sorted(schema.items()))
