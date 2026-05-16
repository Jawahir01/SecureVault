"""SecureVault API package initialization."""

from fastapi import APIRouter

api_router = APIRouter(prefix="/api", tags=["api"])


def register_router(router):
    """Register a sub-router with the main API router."""
    api_router.include_router(router)


__all__ = ["api_router", "register_router"]
