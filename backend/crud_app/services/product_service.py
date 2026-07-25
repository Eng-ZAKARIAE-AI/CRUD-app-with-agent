"""Business logic service layer for Product management."""

from typing import Sequence
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from backend.crud_app.models.product import Product
from backend.crud_app.repositories.product_repository import ProductRepository
from backend.crud_app.schemas.product_schema import ProductCreate, ProductUpdate


class ProductService:
    def __init__(self, repository: ProductRepository, db: Session) -> None:
        self.repository = repository
        self.db = db

    def get_product(self, product_id: int) -> Product:
        product = self.repository.get_by_id(product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {product_id} not found",
            )
        return product

    def list_products(
        self, skip: int = 0, limit: int = 100, active_only: bool = False
    ) -> Sequence[Product]:
        return self.repository.get_all(skip=skip, limit=limit, active_only=active_only)

    def create_product(self, dto: ProductCreate) -> Product:
        if self.repository.get_by_sku(dto.sku):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Product with SKU '{dto.sku}' already exists",
            )
        
        product = Product(**dto.model_dump())
        created_product = self.repository.create(product)
        self.db.commit()
        return created_product

    def update_product(self, product_id: int, dto: ProductUpdate) -> Product:
        product = self.get_product(product_id)
        update_data = dto.model_dump(exclude_unset=True)

        if "sku" in update_data and update_data["sku"] != product.sku:
            if self.repository.get_by_sku(update_data["sku"]):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail=f"Product with SKU '{update_data['sku']}' already exists",
                )

        updated_product = self.repository.update(product, **update_data)
        self.db.commit()
        return updated_product

    def delete_product(self, product_id: int, soft: bool = True) -> None:
        product = self.get_product(product_id)
        if soft:
            self.repository.soft_delete(product)
        else:
            self.repository.delete(product)
        self.db.commit()