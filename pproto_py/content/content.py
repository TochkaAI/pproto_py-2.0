from uuid import UUID
from pydantic import BaseModel

from pproto_py.schemas import BaseMessage, Type
from pproto_py.client import Client
from pproto_py.core.exceptions import TypeMessageError


class BaseContent(BaseModel):
    async def send(self, server: Client, **message_params) -> UUID:
        message = BaseMessage(**message_params, content=self)
        callable_func = {"answer": self.answer, "error": self.error, "failed": self.failed, "unknown": self.unknown}
        if message.flags.type.value != Type.EVENT.value:
            await server.write_with_callback(message, callable_func)
        else:
            await server.write(message)
        return message.id

    async def answer() -> None:
        pass

    async def failed() -> None:
        pass

    async def error() -> None:
        pass

    async def unknown() -> None:
        pass

    async def send_wa(self, server: Client, **message_params):
        message = BaseMessage(**message_params, content=self)
        if message.flags.type.value == Type.EVENT:
            raise TypeMessageError("Event don't have a answer!")
        pass
