from fastapi import APIRouter, status

from src.api.schemas import BaseResponseBody, BaseExceptionBody


router = APIRouter(prefix="/api/v1/healthcheck", tags=["Healthcheck"])


@router.get(
    "/",
    response_model=BaseResponseBody,
    status_code=status.HTTP_200_OK,
    summary="Healthcheck",
)
async def get_readiness_status() -> BaseResponseBody | BaseExceptionBody:
    return BaseResponseBody(data={"status": "ok"})
