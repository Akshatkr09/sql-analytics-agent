"""Create and populate a local sample analytics database."""
from datetime import date
from sqlalchemy import select
from app.database.connection import get_engine
from app.database.schema import metadata, customers, products, orders, order_items

def seed_database(engine=None) -> None:
    engine = engine or get_engine()
    metadata.create_all(engine)
    with engine.begin() as conn:
        if conn.execute(select(customers.c.customer_id).limit(1)).first() is None:
            conn.execute(customers.insert(), [
                {"customer_id":1,"name":"Aarav Sharma","city":"Patna","email":"aarav@example.com"},
                {"customer_id":2,"name":"Meera Singh","city":"Bhopal","email":"meera@example.com"},
                {"customer_id":3,"name":"Kabir Das","city":"Kolkata","email":"kabir@example.com"},
                {"customer_id":4,"name":"Ananya Roy","city":"Bhubaneswar","email":"ananya@example.com"}])
        if conn.execute(select(products.c.product_id).limit(1)).first() is None:
            conn.execute(products.insert(), [
                {"product_id":1,"product_name":"Wireless Mouse","category":"Accessories","price":799.0},
                {"product_id":2,"product_name":"Mechanical Keyboard","category":"Accessories","price":2499.0},
                {"product_id":3,"product_name":"Laptop Stand","category":"Workspace","price":1299.0},
                {"product_id":4,"product_name":"USB-C Hub","category":"Accessories","price":1899.0}])
        if conn.execute(select(orders.c.id).limit(1)).first() is None:
            conn.execute(orders.insert(), [
                {"id":1,"customer_id":1,"order_date":date(2026,1,12),"total_amount":3298.0,"status":"Delivered"},
                {"id":2,"customer_id":2,"order_date":date(2026,1,18),"total_amount":799.0,"status":"Delivered"},
                {"id":3,"customer_id":3,"order_date":date(2026,2,3),"total_amount":3798.0,"status":"Pending"},
                {"id":4,"customer_id":1,"order_date":date(2026,2,21),"total_amount":1299.0,"status":"Shipped"},
                {"id":5,"customer_id":4,"order_date":date(2026,3,7),"total_amount":2499.0,"status":"Delivered"},
                {"id":6,"customer_id":2,"order_date":date(2026,3,15),"total_amount":1899.0,"status":"Pending"}])
        if conn.execute(select(order_items.c.item_id).limit(1)).first() is None:
            conn.execute(order_items.insert(), [
                {"item_id":1,"order_id":1,"product_id":2,"quantity":1,"unit_price":2499.0},
                {"item_id":2,"order_id":1,"product_id":1,"quantity":1,"unit_price":799.0},
                {"item_id":3,"order_id":2,"product_id":1,"quantity":1,"unit_price":799.0},
                {"item_id":4,"order_id":3,"product_id":2,"quantity":1,"unit_price":2499.0},
                {"item_id":5,"order_id":3,"product_id":4,"quantity":1,"unit_price":1299.0},
                {"item_id":6,"order_id":4,"product_id":3,"quantity":1,"unit_price":1299.0},
                {"item_id":7,"order_id":5,"product_id":2,"quantity":1,"unit_price":2499.0},
                {"item_id":8,"order_id":6,"product_id":4,"quantity":1,"unit_price":1899.0}])

if __name__ == "__main__":
    seed_database()
    print("Sample database created and seeded successfully.")
