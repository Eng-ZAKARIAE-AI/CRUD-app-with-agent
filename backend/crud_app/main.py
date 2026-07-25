"""FastAPI application entrypoint for the Product CRUD API."""

from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI

from backend.ai_agent.router import router as agent_router
from backend.crud_app.controllers.product_controller import router as product_router
from backend.crud_app.database import engine
from backend.crud_app.models.product import Base


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle events manager for startup and shutdown tasks."""
    # Initialize database tables on application startup
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Product CRUD API",
    description="REST API for product inventory management and multimodal AI agent",
    version="0.1.0",
    lifespan=lifespan,
)

# Register endpoints
app.include_router(product_router)
app.include_router(agent_router)


@app.get("/health", tags=["Health"])
def health_check() -> Dict[str, str]:
    """Simple health check endpoint."""
    return {"status": "ok"}