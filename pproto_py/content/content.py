from typing import ClassVar
from uuid import UUID

from pydantic import BaseModel

from pproto_py.client import Client
from pproto_py.content.config import ContentConfig
from pproto_py.core.exceptions import ErrorResponseError, TypeMessageError
from pproto_py.schemas import BaseMessage, Type


class BaseContent(BaseModel):
    content_config: ClassVar[ContentConfig] = ContentConfig()

    async def send(self, server: Client, **message_params) -> UUID:
        content = None if self.content_config.get("empty_content", False) else self
        message = BaseMessage(**message_params, content=content)
        callable_func = {"answer": self.answer, "error": self.error, "failed": self.failed, "unknown": self.unknown}
        if message.flags.type.value != Type.EVENT.value:
            await server.write_with_callback(message, callable_func)
        else:
            await server.write(message)
        return message.id

    async def answer(self, content: BaseModel) -> None:
        pass

    async def failed(self, content: BaseModel) -> None:
        pass

    async def error(self, content: BaseModel) -> None:
        pass

    async def unknown(self, content: BaseModel) -> None:
        pass

    async def send_wa(self, server: Client, **message_params):
        async def answer(content: BaseModel):
            return content

        content = None if self.content_config.get("empty_content", False) else self
        message = BaseMessage(**message_params, content=content)
        if message.flags.type.value == Type.EVENT:
            raise TypeMessageError("Event don't have a answer!")
        return await server.write_with_callback(
            message,
            {
                "answer": answer,
                "error": lambda msg: (_ for _ in ()).throw(ErrorResponseError(msg)),
            },
        )
