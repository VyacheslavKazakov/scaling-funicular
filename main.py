import logging
from contextlib import asynccontextmanager
from logging import config as logging_config
from typing import AsyncIterator, Callable, Any

import uvicorn
from fastapi import APIRouter, FastAPI, Request
from fastapi.responses import ORJSONResponse
from redis.asyncio import Redis
from redis.backoff import ExponentialBackoff
from redis.exceptions import BusyLoadingError, ConnectionError, TimeoutError
from redis.asyncio.retry import Retry
from starlette.middleware.cors import CORSMiddleware
import src.constants as const
from src.api.schemas import BaseExceptionBody
from src.api.v1.answers.routers import router as answers_router
from src.api.v1.healthcheck.routers import router as healthcheck_router

from src.core.config import settings
from src.core.logger import LOGGING
from src.db import caches

logging_config.dictConfig(LOGGING)
logger = logging.getLogger(__name__)

v1_router = APIRouter(
    responses={
        404: {"model": BaseExceptionBody},
        400: {"model": BaseExceptionBody},
    },
)

v1_router.include_router(answers_router)
v1_router.include_router(healthcheck_router)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    caches.cache = caches.RedisCacheStorage(
        client=Redis(
            host=settings.cache_host,
            port=settings.cache_port,
            db=settings.cache_db,
            retry=Retry(
                ExponentialBackoff(cap=10, base=0.1),
                retries=5,
            ),
            retry_on_error=[BusyLoadingError, ConnectionError, TimeoutError],
        )
    )

    yield

    await caches.cache.close()


app = FastAPI(
    title=const.APP_API_DOCS_TITLE,
    version=const.APP_VERSION,
    description=const.APP_DESCRIPTION,
    docs_url="/api/v1/docs",
    openapi_url="/api/v1/docs.json",
    default_response_class=ORJSONResponse,
    lifespan=lifespan,
    swagger_ui_parameters={"defaultModelsExpandDepth": 0},
)

app.include_router(v1_router)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_hosts,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        workers=settings.workers,
        reload=settings.debug,
    )
