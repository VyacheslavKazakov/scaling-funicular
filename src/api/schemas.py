import logging
from typing import Any, Generic, TypeVar

from pydantic import BaseModel


logger = logging.getLogger(__name__)

DataType = TypeVar("DataType")


class BaseResponseBody(BaseModel, Generic[DataType]):
    data: DataType | None = None


class BaseExceptionBody(BaseModel):
    data: dict[str, Any] | None = None
