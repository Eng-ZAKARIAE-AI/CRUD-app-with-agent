"""FastAPI Controller/Router for Product REST API endpoints."""

from typing import List, Optional
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

# Import database dependency provider (adjust path according to your setup)
from backend.crud_app.database import get_db
from backend.crud_app.repositories.product_repository import ProductRepository
from backend.crud_app.schemas.product_schema import (
    ProductCreate,
    ProductResponse,
    ProductUpdate,
)
from backend.crud_app.services.product_service import ProductService

router = APIRouter(prefix="/products", tags=["Products"])


def get_product_service(db: Session = Depends(get_db)) -> ProductService:
    """Dependency injection factory for ProductService."""
    repo = ProductRepository(db)
    return ProductService(repository=repo, db=db)


@router.get(
    "/",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List products",
)
def list_products(
    skip: int = Query(0, ge=0, description="Offset pagination skip index"),
    limit: int = Query(100, ge=1, le=500, description="Page limit max 500"),
    active_only: bool = Query(False, description="Filter for active products only"),
    service: ProductService = Depends(get_product_service),
):
    """Retrieve a list of products with optional pagination and active filters."""
    return service.list_products(skip=skip, limit=limit, active_only=active_only)


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
)
def get_product(
    product_id: int,
    service: ProductService = Depends(get_product_service),
):
    """Retrieve details of a single product by its unique identifier."""
    return service.get_product(product_id)


@router.post(
    "/",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
)
def create_product(
    dto: ProductCreate,
    service: ProductService = Depends(get_product_service),
):
    """Create and persist a new product record."""
    return service.create_product(dto)


@router.patch(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product",
)
def update_product(
    product_id: int,
    dto: ProductUpdate,
    service: ProductService = Depends(get_product_service),
):
    """Partially update an existing product record."""
    return service.update_product(product_id, dto)


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
)
def delete_product(
    product_id: int,
    soft: bool = Query(True, description="Perform soft delete (deactivate) if True"),
    service: ProductService = Depends(get_product_service),
):
    """Delete a product from the system (Soft delete enabled by default)."""
    service.delete_product(product_id, soft=soft)
    return None