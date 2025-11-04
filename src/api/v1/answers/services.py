import logging

from fastapi import Depends

from src.api.v1.answers.handlers import LLMAnswerHandler, get_llm_answer_handler

logger = logging.getLogger(__name__)


class AnswerService:
    _namespace = "answers"

    def __init__(self, llm_answer_handler: LLMAnswerHandler) -> None:
        self.llm_answer_handler = llm_answer_handler

    async def get_answer(self, question: str):
        answer = await self.llm_answer_handler.handle(question=question)
        return answer


def get_answer_service(
    llm_answer_handler: LLMAnswerHandler = Depends(get_llm_answer_handler),
) -> AnswerService:
    return AnswerService(llm_answer_handler=llm_answer_handler)
