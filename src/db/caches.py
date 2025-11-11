import hashlib
import logging
from functools import wraps
from typing import Optional, Any

import orjson
from redis.asyncio import Redis

from src.core.config import settings

logger = logging.getLogger(__name__)


class RedisCacheStorage:
    def __init__(self, client: Redis) -> None:
        self.client = client

    async def get_object(self, obj_id: str | int | None = None) -> str | None:
        return await self.client.get(obj_id)

    async def set_object(self, source: str, **kwargs) -> None:
        await self.client.set(name=source, **kwargs)

    async def close(self) -> None:
        await self.client.close()


def get_cache_key(namespace: str, *args, **kwargs) -> str:
    prepare_mark: list[str] = []
    if args:
        prepare_mark.extend(map(str, args))
    if kwargs:
        prepare_mark.extend([f"{k}:{v}" for k, v in kwargs.items()])
    mark_str_encoded = ":".join(prepare_mark).encode("utf-8")
    mark = hashlib.md5(mark_str_encoded).hexdigest()
    logger.debug(
        f"Cache key: namespace: {namespace}, params: {args}, {kwargs}, prepare: {prepare_mark}, hash: {mark}"
    )
    return f"{settings.cache_prefix}:{namespace}:{mark}"


def cache_deco(
    namespace: Optional[str] = "",
    expire_in_seconds: int = settings.cache_ttl_in_seconds,
) -> Any:
    def func_wrapper(func):
        @wraps(func)
        async def wrapper(cls, *args, **kwargs):
            cache_key = get_cache_key(namespace, *args, **kwargs)
            data = await cache.get_object(cache_key) if cache else None
            if data:
                data = orjson.loads(data)
            else:
                data = await func(cls, *args, **kwargs)
                if cache:
                    await cache.set_object(
                        source=cache_key,
                        value=orjson.dumps(data),
                        ex=expire_in_seconds,
                    )
            return data

        return wrapper

    return func_wrapper


cache: RedisCacheStorage | None = None
