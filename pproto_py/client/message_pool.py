import asyncio
from typing import TypeVar

from pproto_py.schemas import BaseMessage
from pproto_py.core.exceptions import CommandTimeLifeOutError

MessageKeyT = TypeVar("MessageKeyT")


class MessagePool(dict[MessageKeyT, BaseMessage]):
    _pending: dict[MessageKeyT, asyncio.Event] = {}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    async def __getitem__(self, key):
        try:
            return super().__getitem__(key)
        except KeyError:
            pass
        if key not in self._pending:
            self._pending[key] = asyncio.Event()
        event = self._pending[key]
        try:
            await event.wait()
        finally:
            if key in self._pending:
                self._pending.pop(key)
                event.clear()
        return super().__getitem__(key)

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if key in self._pending:
            self._pending.pop(key).set()

    def add_message(self, message: BaseMessage):
        self[message.id] = message

    def dell_message(self, message: BaseMessage):
        if (message_id := message.id) in self:
            super().__delitem__(message_id)
        else:
            raise KeyError("Message does not exist in MessagePool")

    def is_waiting(self, message_id: MessageKeyT) -> bool:
        return message_id in self._pending

    async def get_message(self, message_id: MessageKeyT, timeout=None) -> BaseMessage:
        try:
            async with asyncio.timeout(timeout if timeout != -1 else None):
                return await self.__getitem__(message_id)
        except TimeoutError as err:
            raise CommandTimeLifeOutError(f"Command life-time out {timeout}: {err!r}") from err
