import logging

from fastapi import Depends

from src.api.v1.answers.handlers import LLMAnswerHandler, get_llm_answer_handler
from src.core.config import settings
from src.db.caches import cache_deco

logger = logging.getLogger(__name__)


class AnswerService:
    _namespace = "answers"

    def __init__(self, llm_answer_handler: LLMAnswerHandler) -> None:
        self.llm_answer_handler = llm_answer_handler

    @cache_deco(
        namespace=_namespace,
        expire_in_seconds=settings.cache_ttl_in_seconds,
    )
    async def get_answer(self, question: str):
        answer = await self.llm_answer_handler.handle(question=question)
        return answer


def get_answer_service(
    llm_answer_handler: LLMAnswerHandler = Depends(get_llm_answer_handler),
) -> AnswerService:
    return AnswerService(llm_answer_handler=llm_answer_handler)
