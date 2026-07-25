"""Script to seed initial product data into the database."""

from decimal import Decimal
from backend.crud_app.database import SessionLocal, engine
from backend.crud_app.models.product import Base, Product

def seed_products():
    # Ensure tables are created directly with engine and Base
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()

    try:
        if db.query(Product).count() > 0:
            print("Database already contains product data!")
            return

        sample_products = [
            Product(
                name="Wireless Ergonomic Mouse",
                sku="WM-2001",
                price=Decimal("29.99"),
                description="2.4GHz optical wireless mouse with adjustable DPI.",
                stock_quantity=45,
                is_active=True,
            ),
            Product(
                name="Mechanical Gaming Keyboard",
                sku="KB-1080",
                price=Decimal("89.99"),
                description="RGB back-lit mechanical keyboard with tactile blue switches.",
                stock_quantity=30,
                is_active=True,
            ),
            Product(
                name="27-inch 4K Monitor",
                sku="MN-4K27",
                price=Decimal("349.50"),
                description="IPS panel, 144Hz refresh rate, HDR400 support.",
                stock_quantity=12,
                is_active=True,
            ),
            Product(
                name="Noise-Canceling Headphones",
                sku="HP-NC700",
                price=Decimal("199.00"),
                description="Over-ear wireless headphones with active noise cancellation.",
                stock_quantity=20,
                is_active=True,
            ),
        ]

        db.add_all(sample_products)
        db.commit()
        print(f"Successfully added {len(sample_products)} products to the database!")

    except Exception as e:
        db.rollback()
        print(f"An error occurred: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_products()