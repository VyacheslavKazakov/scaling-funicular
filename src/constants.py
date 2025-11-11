import os
from contextvars import ContextVar

ENV = os.environ.get("ENV", "dev")
APP_VERSION = "0.0.1"
APP_PREFIX = "Math API"
APP_NAME = "MathAPI"
APP_DESCRIPTION = "Solve math problems with AI support"
APP_API_DOCS_TITLE = f"{APP_NAME} ({ENV.upper()})" if ENV != "dev" else APP_NAME

REQUEST_ID_IN_CONTEXT: ContextVar[str] = ContextVar("request_id", default="")
