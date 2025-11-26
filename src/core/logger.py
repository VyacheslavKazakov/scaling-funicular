import logging

from opentelemetry import trace

from src.core.config import settings
from src.constants import REQUEST_ID_IN_CONTEXT


class RequestIDFilter(logging.Filter):
    """Add request_id and trace_id from context to log records."""

    def filter(self, record):
        record.request_id = REQUEST_ID_IN_CONTEXT.get()

        # Add trace_id from OpenTelemetry context if tracing is enabled
        if settings.enable_tracing:
            span = trace.get_current_span()
            if span and span.get_span_context().is_valid:
                trace_id = format(span.get_span_context().trace_id, "032x")
                record.trace_id = trace_id
            else:
                record.trace_id = ""
        else:
            record.trace_id = ""

        return True


LOG_LEVEL = settings.log_level
LOG_FORMAT = "%(asctime)s - [%(request_id)s] - trace_id=%(trace_id)s - %(name)s - %(levelname)s - %(message)s"
LOG_DEFAULT_HANDLERS = ["console"]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "verbose": {"format": LOG_FORMAT},
        "default": {
            "()": "uvicorn.logging.DefaultFormatter",
            "fmt": "%(levelprefix)s %(message)s",
            "use_colors": None,
        },
        "access": {
            "()": "uvicorn.logging.AccessFormatter",
            "fmt": "%(asctime)s - [%(request_id)s] - %(name)s - %(levelname)s - %(message)s "
            "%(status_code)s",
        },
    },
    "filters": {
        "request_id": {
            "()": RequestIDFilter,
        },
    },
    "handlers": {
        "console": {
            "level": "DEBUG",
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["request_id"],
        },
        "default": {
            "formatter": "default",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["request_id"],
        },
        "access": {
            "formatter": "access",
            "class": "logging.StreamHandler",
            "stream": "ext://sys.stdout",
            "filters": ["request_id"],
        },
    },
    "loggers": {
        "": {
            "handlers": LOG_DEFAULT_HANDLERS,
            "level": LOG_LEVEL,
        },
        "uvicorn.error": {
            "level": LOG_LEVEL,
        },
        "uvicorn.access": {
            "handlers": ["access"],
            "level": LOG_LEVEL,
            "propagate": False,
        },
        # Suppress OpenTelemetry attribute warnings from LangGraph
        "opentelemetry.attributes": {
            "level": "ERROR",
            "propagate": False,
        },
    },
    "root": {
        "level": LOG_LEVEL,
        "formatter": "verbose",
        "handlers": LOG_DEFAULT_HANDLERS,
    },
}
