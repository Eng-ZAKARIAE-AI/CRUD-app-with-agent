"""Product Domain Model using SQLAlchemy 2.0 declarative Mapped syntax."""

from datetime import datetime, timezone
from decimal import Decimal
from typing import Optional

from sqlalchemy import DateTime, Index, Numeric, String, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, MappedAsDataclass, mapped_column


class Base(MappedAsDataclass, DeclarativeBase):
    """Abstract Base Class enabling dataclass features across all models."""

    pass


class Product(Base):
    """
    Product Entity representing the core domain object for inventory/catalog.
    
    Combines SQLAlchemy 2.0 type mapping with Python dataclass instantiation.
    """

    __tablename__ = "products"

    # --- PRIMARY KEY ---
    id: Mapped[int] = mapped_column(
        primary_key=True,
        autoincrement=True,
        init=False,  # Managed by DB engine on insertion
    )

    # --- CORE ATTRIBUTES ---
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        comment="Human-readable product name",
    )

    sku: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        comment="Stock Keeping Unit (Unique Identifier for inventory)",
    )

    price: Mapped[Decimal] = mapped_column(
        Numeric(precision=10, scale=2),
        nullable=False,
        comment="Unit price stored as exact numeric representation",
    )

    # --- OPTIONAL / DEFAULTED ATTRIBUTES ---
    description: Mapped[Optional[str]] = mapped_column(
        Text,
        default=None,
        nullable=True,
    )

    stock_quantity: Mapped[int] = mapped_column(
        default=0,
        nullable=False,
    )

    is_active: Mapped[bool] = mapped_column(
        default=True,
        nullable=False,
        index=True,
    )

    # --- AUDIT TIMESTAMPS ---
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        init=False,
        server_default=func.now(),
        nullable=False,
    )

    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        init=False,
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # --- COMPOSITE INDEXES ---
    __table_args__ = (
        Index("ix_products_active_stock", "is_active", "stock_quantity"),
    )

    def __repr__(self) -> str:
        return (
            f"Product(id={getattr(self, 'id', None)!r}, "
            f"sku={self.sku!r}, name={self.name!r}, price={self.price!r})"
        )