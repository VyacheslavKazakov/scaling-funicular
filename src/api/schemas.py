import logging
from typing import Any

from pydantic import BaseModel


logger = logging.getLogger(__name__)


class BaseExceptionBody(BaseModel):
    data: dict[str, Any] | None = None
