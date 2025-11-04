import logging
from contextlib import asynccontextmanager
from logging import config as logging_config
from typing import AsyncIterator, Callable, Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import ORJSONResponse
from starlette.middleware.cors import CORSMiddleware
from starlette.middleware.sessions import SessionMiddleware
import src.constants as const
from src.api.schemas import BaseExceptionBody
from src.api.v1.answers.routers import router as answers_router

from src.core.config import settings
from src.core.logger import LOGGING


logging_config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

v1_router = APIRouter(
    responses={
        404: {"model": BaseExceptionBody},
        400: {"model": BaseExceptionBody},
    },
)

v1_router.include_router(answers_router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    yield


app = FastAPI(
    title=const.APP_API_DOCS_TITLE,
    version=const.APP_VERSION,
    description=const.APP_DESCRIPTION,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/docs.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    swagger_ui_parameters={
        "defaultModelsExpandDepth": 0
    },  # -1 value hides the Schemas section from the docs
)

app.include_router(v1_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(SessionMiddleware, secret_key=settings.secret_key)


@app.middleware("http")
async def request_id_middleware(request: Request, call_next: Callable[..., Any]) -> Any:
    request_id = request.headers.get("X-Request-Id", "")
    const.REQUEST_ID_IN_CONTEXT.set(request_id)
    return await call_next(request)


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host=settings.listen_addr,
        port=settings.listen_port,
        log_config=LOGGING,
        log_level=settings.log_level.lower(),
        reload=True,
    )
