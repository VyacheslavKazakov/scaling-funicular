from abc import ABC, abstractmethod
from typing import Any


class CacheBaseStorage(ABC):
    def __init__(self, client: Any, **kwargs) -> None:
        self.client = client

    @abstractmethod
    async def get_object(self, source: str, obj_id: str | int | None = None, **kwargs) -> str | None:
        raise NotImplementedError

    @abstractmethod
    async def set_object(self, source: str, **kwargs) -> None:
        raise NotImplementedError
