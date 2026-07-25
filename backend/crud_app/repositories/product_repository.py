"""Repository layer for managing Product entity persistence operations."""

from decimal import Decimal
from typing import Optional, Sequence

from sqlalchemy import select, func
from sqlalchemy.orm import Session

from backend.crud_app.models.product import Product


class ProductRepository:
    """Encapsulates database operations for the Product model."""

    def __init__(self, db: Session) -> None:
        self.db = db

    # --- READ OPERATIONS ---

    def get_by_id(self, product_id: int) -> Optional[Product]:
        """Fetch a single product by its primary key ID."""
        return self.db.get(Product, product_id)

    def get_by_sku(self, sku: str) -> Optional[Product]:
        """Fetch a single product by its unique SKU."""
        stmt = select(Product).where(Product.sku == sku)
        return self.db.scalars(stmt).first()

    def get_all(
        self, 
        skip: int = 0, 
        limit: int = 100, 
        active_only: bool = False
    ) -> Sequence[Product]:
        """
        Fetch a paginated list of products.
        
        :param skip: Number of records to offset.
        :param limit: Maximum number of records to return.
        :param active_only: If True, filters out inactive products.
        """
        stmt = select(Product)
        if active_only:
            stmt = stmt.where(Product.is_active == True)  # noqa: E712
            
        stmt = stmt.order_by(Product.id.desc()).offset(skip).limit(limit)
        return self.db.scalars(stmt).all()

    def count(self, active_only: bool = False) -> int:
        """Count total product records in the database."""
        stmt = select(func.count(Product.id))
        if active_only:
            stmt = stmt.where(Product.is_active == True)  # noqa: E712
        return self.db.scalar(stmt) or 0

    # --- WRITE OPERATIONS ---

    def create(self, product: Product) -> Product:
        """
        Persist a new Product instance into the database.
        
        Note: Commit and rollback are left to the caller/unit-of-work layer 
        or service dependency for transaction integrity.
        """
        self.db.add(product)
        self.db.flush()  # Flushes to populate the DB-generated ID without committing
        self.db.refresh(product)
        return product

    def update(self, product: Product, **kwargs) -> Product:
        """Dynamically update fields of an existing Product instance."""
        for key, value in kwargs.items():
            if hasattr(product, key) and value is not None:
                setattr(product, key, value)
        self.db.flush()
        self.db.refresh(product)
        return product

    def update_stock(self, product_id: int, quantity_change: int) -> Optional[Product]:
        """Increment or decrement stock quantity for a given product."""
        product = self.get_by_id(product_id)
        if product:
            product.stock_quantity += quantity_change
            self.db.flush()
            self.db.refresh(product)
        return product

    def delete(self, product: Product) -> None:
        """Hard delete a Product from the database."""
        self.db.delete(product)
        self.db.flush()

    def soft_delete(self, product: Product) -> Product:
        """Soft delete a Product by setting is_active to False."""
        product.is_active = False
        self.db.flush()
        self.db.refresh(product)
        return product