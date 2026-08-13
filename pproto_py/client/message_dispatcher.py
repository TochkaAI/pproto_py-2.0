import asyncio
from enum import StrEnum
from uuid import UUID
from typing import Callable, Awaitable
import logging
from collections import defaultdict

from pproto_py.schemas import BaseMessage


logger = logging.getLogger(__name__)

MessageHandler = Callable[[BaseMessage], Awaitable[None]]


class MessageDispatcher:
    def __init__(self) -> None:
        self._commands_handlers: dict[UUID, list[MessageHandler]] = defaultdict(list)
        self._events_handlers: dict[UUID, list[MessageHandler]] = defaultdict(list)

    def subscribe(self, command: UUID | StrEnum | str, handler: MessageHandler) -> Callable[[], None]:
        _command = UUID(command) if isinstance(command, (StrEnum, str)) else command
        self._commands_handlers[_command].append(handler)

        def unsubscribe() -> None:
            self._commands_handlers[_command].remove(handler)

        return unsubscribe

    async def dispatch(self, message: BaseMessage) -> None:
        handlers = self._commands_handlers.get(message.command, [])
        for handler in handlers:
            asyncio.create_task(self._safe_call(handler, message))

    @staticmethod
    async def _safe_call(handler: MessageHandler, message: BaseMessage) -> None:
        try:
            await handler(message)
        except Exception:
            logger.exception(f"Error while handling message: {message}")
