from pydantic import BaseModel, Field


class AnswerGetSchema(BaseModel):
    answer: str | int | float | list[int | float] | None = Field(..., examples=["42"])


class LLMAnswerSchema(BaseModel):
    answer: str | int | float | list[int | float] | None = Field(
        default=None, examples=["42"]
    )
