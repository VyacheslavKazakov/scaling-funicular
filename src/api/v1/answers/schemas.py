from pydantic import BaseModel, Field


class AnswerGetSchema(BaseModel):
    answer: str = Field(..., examples=["42"])
