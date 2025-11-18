from openai import AsyncOpenAI
from src.api.v1.answers.prompts import MATH_PROBLEM_PROMPT
from src.api.v1.answers.schemas import LLMAnswerSchema
from src.core.config import settings
from functools import lru_cache


class LLMAnswerHandler:
    def __init__(self) -> None:
        self._llm = AsyncOpenAI(
            api_key=settings.openai_api_key,
        )

    async def handle(self, question: str):
        answer = await self._llm.chat.completions.parse(
            model=settings.default_model,
            messages=[
                {"content": MATH_PROBLEM_PROMPT, "role": "system"},
                {"content": question, "role": "user"},
            ],
            response_format=LLMAnswerSchema,
        )
        parsed = answer.choices[0].message.parsed
        return parsed.answer


@lru_cache(maxsize=1)
def get_llm_answer_handler() -> LLMAnswerHandler:
    return LLMAnswerHandler()
