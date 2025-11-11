from typing import Callable

from langchain_core.tools import BaseTool
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent

from src.api.v1.answers.prompts import MATH_PROBLEM_PROMPT
from src.api.v1.answers.schemas import LLMAnswerSchema
from src.api.v1.answers.tools import safe_execute_code_tool
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
        self._tools: list[
            Callable[[str | int | float], str | int | float] | BaseTool
        ] = [safe_execute_code_tool]
        self._agent = create_agent(
            model=self._llm,
            tools=self._tools,
            response_format=LLMAnswerSchema,
            debug=settings.debug,
        )

    async def handle(self, question: str):
        answer = await self._agent.ainvoke(
            {
                "messages": [
                    {"content": MATH_PROBLEM_PROMPT, "role": "system"},
                    {"content": question, "role": "user"},
                ]
            }
        )
        return answer.get("structured_response", LLMAnswerSchema()).answer


@lru_cache(maxsize=1)
def get_llm_answer_handler() -> LLMAnswerHandler:
    return LLMAnswerHandler()
