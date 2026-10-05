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
                "answer": answer if "answer" not in type(self).__dict__ else self.answer,
                "error": lambda msg: (_ for _ in ()).throw(ErrorResponseError(msg)),
            },
        )

    async def send_with_answer(self, server: Client, **message_params):
        return await self.send_wa(server, **message_params)

    async def send_with_message_response(self, server: Client, **message_params) -> BaseMessage:
        content = None if self.content_config.get("empty_content", False) else self
        message = BaseMessage(**message_params, content=content)
        if message.flags.type.value == Type.EVENT:
            raise TypeMessageError("Event don't have a answer!")
        return await server.with_message_response(message)
