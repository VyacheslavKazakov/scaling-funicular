from typing import Callable

from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from src.api.v1.answers.schemas import LLMAnswerSchema
from src.core.config import settings


class LLMAnswerHandler:
    def __init__(self) -> None:
        self._llm = ChatOpenAI(
            model=settings.default_model,
            api_key=settings.openai_api_key,
            max_tokens=settings.default_max_tokens,
            temperature=settings.default_temperature,
        )
        self._tools: list[Callable[[str | int | float], str | int | float]] = []
        self._agent = create_agent(
            model=self._llm,
            system_prompt=settings.default_prompt,
            tools=self._tools,
            response_format=LLMAnswerSchema,
            debug=settings.debug,
        )

    async def handle(self, question: str):
        answer = await self._agent.ainvoke(
            {"messages": [{"content": question, "role": "user"}]}  # noqa
        )
        return answer.get("structured_response", LLMAnswerSchema()).answer


def get_llm_answer_handler() -> LLMAnswerHandler:
    return LLMAnswerHandler()
