import logging
from typing import Annotated

from fastapi import APIRouter, status, Depends, Query

from src.api.v1.answers.schemas import AnswerGetSchema
from src.api.v1.answers.services import AnswerService, get_answer_service

router = APIRouter(prefix="/get_answer", tags=["Answers"])
logger = logging.getLogger(__name__)


@router.get(
    "/",
    summary="Get answer.",
    status_code=status.HTTP_200_OK,
    description="Get answers.",
)
async def get_answer(
    question: Annotated[
        str,
        Query(
            min_length=1,
            max_length=2048,
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
