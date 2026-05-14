"""Retry helpers with exponential backoff."""
from __future__ import annotations

import asyncio
import logging
from typing import Awaitable, Callable, Tuple, Type, TypeVar

logger = logging.getLogger(__name__)

T = TypeVar("T")


async def retry_async(
    fn: Callable[[], Awaitable[T]],
    *,
    attempts: int = 3,
    base_delay: float = 0.5,
    max_delay: float = 4.0,
    retry_on: Tuple[Type[BaseException], ...] = (Exception,),
    label: str = "operation",
) -> T:
    """Call `fn` up to `attempts` times with exponential backoff.

    Raises the final exception if every attempt fails.
    """
    last_exc: BaseException | None = None
    for i in range(max(1, attempts)):
        try:
            return await fn()
        except retry_on as e:
            last_exc = e
            if i + 1 >= attempts:
                break
            delay = min(max_delay, base_delay * (2 ** i))
            logger.warning(
                "%s failed (attempt %d/%d): %s — retrying in %.1fs",
                label, i + 1, attempts, e, delay,
            )
            await asyncio.sleep(delay)
    # Re-raise the final error so the caller can decide how to surface it
    assert last_exc is not None
    raise last_exc
