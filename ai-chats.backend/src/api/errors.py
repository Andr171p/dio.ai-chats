from ddf.application.exceptions import ApplicationError
from ddf.domain.exceptions import DomainError
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


async def handle_error(request: Request, error: Exception) -> JSONResponse:
    if not isinstance(error, (ApplicationError, DomainError)):
        raise error

    return JSONResponse(
        status_code=error.status_code,
        content={"error": {"code": error.error_code, "message": error.message, "details": error.details}},
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(ApplicationError, handle_error)
    app.add_exception_handler(DomainError, handle_error)
