import logging

from fastapi import Request, status
from fastapi.responses import ORJSONResponse
from prometheus_client import Counter

import src.constants as const

logger = logging.getLogger(__name__)

fastapi_exceptions_total = Counter(
    "fastapi_exceptions_total",
    "Total number of unhandled exceptions",
    ["exception_type"],
)


async def global_exception_handler(request: Request, exc: Exception) -> ORJSONResponse:
    """
    Global exception handler that tracks all unhandled exceptions
    and returns a consistent error response.
    """
    exception_type = type(exc).__name__

    fastapi_exceptions_total.labels(exception_type=exception_type).inc()

    logger.error(
        f"Unhandled exception: {exception_type}: {exc}",
        exc_info=True,
        extra={
            "request_id": const.REQUEST_ID_IN_CONTEXT.get(),
            "path": request.url.path,
            "method": request.method,
            "exception_type": exception_type,
        },
    )

    return ORJSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "data": {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "detail": "Internal server error",
                "type": exception_type,
            }
        },
    )
