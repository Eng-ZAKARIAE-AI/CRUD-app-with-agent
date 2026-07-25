"""Pydantic schemas for Product validation and serialization."""

from datetime import datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(
        ...,
        min_length=1,
        max_length=150,
        json_schema_extra={"examples": ["Wireless Mouse"]},
    )
    sku: str = Field(
        ...,
        min_length=1,
        max_length=50,
        json_schema_extra={"examples": ["WM-1029"]},
    )
    price: Decimal = Field(
        ...,
        gt=0,
        decimal_places=2,
        json_schema_extra={"examples": [29.99]},
    )
    description: Optional[str] = Field(
        None,
        json_schema_extra={"examples": ["Ergonomic optical wireless mouse."]},
    )
    stock_quantity: int = Field(0, ge=0, json_schema_extra={"examples": [50]})
    is_active: bool = Field(True)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    price: Optional[Decimal] = Field(None, gt=0, decimal_places=2)
    description: Optional[str] = None
    stock_quantity: Optional[int] = Field(None, ge=0)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime
    updated_at: datetime
