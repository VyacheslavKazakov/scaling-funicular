import logging
from typing import Annotated

from fastapi import APIRouter, status, Depends, Query
from starlette.requests import Request

from src.core.limiters import limiter
from src.api.v1.answers.schemas import AnswerGetSchema
from src.api.v1.answers.services import AnswerService, get_answer_service
from src.core.config import settings

router = APIRouter(tags=["Answers"])
logger = logging.getLogger(__name__)


@router.get(
    "/get_answer",
    summary="Get answer.",
    status_code=status.HTTP_200_OK,
    description="Get answers.",
)
@limiter.limit(settings.rate_limit)
async def get_answer(
    request: Request,
    question: Annotated[
        str,
        Query(
            min_length=1,
            max_length=settings.question_max_length,
            description="Mathematical question or problem to solve",
            examples=[
                "Calculate the area of a circle with radius 5",
                "Find the derivative of x^2 at x=3",
            ],
        ),
    ],
    service: Annotated[AnswerService, Depends(get_answer_service)],
) -> AnswerGetSchema:
    answer = await service.get_answer(question=question)
    return AnswerGetSchema(answer=answer)
