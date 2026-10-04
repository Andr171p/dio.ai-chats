from fastapi import APIRouter

from . import conversations, mcp_connections, mcp_servers, model_connections, models

router = APIRouter(prefix="/api/v1")
router.include_router(model_connections.router)
router.include_router(models.router)
router.include_router(mcp_connections.router)
router.include_router(mcp_servers.router)
router.include_router(conversations.router)

__all__ = ["router"]
