from fastapi import FastAPI

from src.bootstrap import lifespan

from .errors import register_exception_handlers
from .v1 import router as v1_router


def create_app() -> FastAPI:
    app = FastAPI(title="DIO AI Chats", version="0.1.0", lifespan=lifespan)

    app.include_router(v1_router)
    register_exception_handlers(app)

    return app
