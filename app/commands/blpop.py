"""BLPOP command implementation."""

import asyncio
from typing import Any, Optional

from app.blocking import register_waiter, unregister_waiter
from app.exceptions import WrongTypeError
from app.storage import get_storage

from .base import BaseCommand


class BlpopCommand(BaseCommand):
    """
    BLPOP command - Blocking pop from the left of a list.

    Syntax: BLPOP key timeout
    Blocks until an element is available or timeout expires.
    If timeout is 0, blocks indefinitely.
    Returns: Array [key, element] if successful, None if timeout
    """

    @property
    def name(self) -> str:
        return "BLPOP"

    def _try_pop(self, storage, key: str) -> Optional[list[str]]:
        """
        Try to pop an element from the list.

        Returns:
            Array [key, element] if successful, None otherwise
        """
        try:
            result = storage.lpop(key, 1)
            if result and len(result) > 0:
                return [key, result[0]]
        except WrongTypeError:
            pass
        return None

    async def execute(self, args: list[str], connection_id: Any = None) -> Any:
        """
        Execute BLPOP command asynchronously (event-driven, no polling).

        Args:
            args: [key, timeout]

        Returns:
            Array [key, element] if successful, None if timeout expires
        """
        self.validate_args(args, min_args=2, max_args=2)

        key = args[0]

        try:
            timeout = float(args[1])
            if timeout < 0:
                raise ValueError("ERR timeout is negative")
        except ValueError as ex:
            if "negative" in str(ex):
                raise
            raise ValueError("ERR timeout is not a float or out of range") from ex

        storage = get_storage()

        result = self._try_pop(storage, key)
        if result is not None:
            return result

        event = asyncio.Event()
        register_waiter(key, event)

        try:
            if timeout > 0:
                await asyncio.wait_for(event.wait(), timeout=timeout)
            else:
                await event.wait()

            result = self._try_pop(storage, key)
            return result or {"null_array": True}

        except asyncio.TimeoutError:
            return {"null_array": True}
        finally:
            unregister_waiter(key, event)
