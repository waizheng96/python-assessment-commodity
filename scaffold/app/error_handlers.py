import logging

from fastapi import Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("commoditywatch")


def register_error_handlers(app):
    """Fully wired — do not modify. Catches anything that isn't already an
    HTTPException (those are handled by FastAPI's own default handler) and
    returns a clean 500 instead of leaking a stack trace to the client."""

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"},
        )
