from langchain_openai import ChatOpenAI

from src.api.v1.answers.prompts import MATH_PROBLEM_PROMPT
from src.api.v1.answers.schemas import LLMAnswerSchema
from src.core.config import settings
from functools import lru_cache


class LLMAnswerHandler:
    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=settings.default_model,
            api_key=settings.openai_api_key,
            max_tokens=settings.default_max_tokens,
            temperature=settings.default_temperature,
        )
        self._llm_with_structured_output = self._llm.with_structured_output(
            schema=LLMAnswerSchema
        )

    async def handle(self, question: str):
        answer = await self._llm_with_structured_output.ainvoke(
            [
                {"content": MATH_PROBLEM_PROMPT, "role": "system"},
                {"content": question, "role": "user"},
            ]
        )
        return answer.answer


@lru_cache(maxsize=1)
def get_llm_answer_handler() -> LLMAnswerHandler:
    return LLMAnswerHandler()
