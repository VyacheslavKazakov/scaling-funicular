import logging

logger = logging.getLogger(__name__)


class AnswerService:
    _namespace = "answers"

    def __init__(self) -> None: ...

    async def get_answer(self, question: str):
        return f"Question answered: {question}"


def get_answer_service() -> AnswerService:
    return AnswerService()
