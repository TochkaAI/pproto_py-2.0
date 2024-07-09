import traceback
import ast
import zlib
from uuid import UUID, uuid4
from typing import Dict, Callable
from asyncio.streams import StreamReader, StreamWriter
import asyncio

from pproto_py.core import Formats, Commands, PprotoCommonException, FormatsException, logger
from pproto_py.schemas import BaseMessage, FlagMessage, Type, Status, Compression
from pproto_py.content import BaseContent
from pproto_py.base import Base
from .router import Command


class Pproto(asyncio.Protocol, Base):
    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8888,
        format=Formats.JSON_PROTOCOL_FORMAT.value,
        compatible=Commands.Compatible.value,
        use_compress=False,
    ):
        self.__host: str = host
        self.__port: int = port
        self.__format = format
        self.compatible = compatible
        self.routers: Dict[UUID, Command] = {}
        self.exception_handlers: Dict[Exception, Callable] = {}
        # self.middleware_routers: Dict[] = {}
        self.clients: Dict[UUID, (StreamReader, StreamWriter)] = {}
        self.use_compress = use_compress

    async def compatible_message(self, user_id: UUID) -> None:
        __reader, __writer = self.clients[user_id]
        message = BaseMessage(
            command=self.compatible,
            maxTimeLife=5,
        )
        __writer.write(self.swap32_len(message=message))
        await __writer.drain()
        __writer.write(message.model_dump_json().encode())
        await __writer.drain()
        data_size = int.from_bytes(await __reader.read(4), signed=True)
        data_compatible = await __reader.read(data_size)
        # TODO check compatible

    async def hello_message(self, user_id: UUID) -> None:
        format = UUID(self.__format).bytes
        __reader, __writer = self.clients[user_id]
        __writer.write(format)
        await __writer.drain()
        data = await __reader.read(16)
        if data != format:
            raise FormatsException(error="The server format is different from the client")

    async def __handle_coroutine(self, reader: StreamReader, writer: StreamWriter):
        await logger.info("INFO -- New client connected")
        try:
            user_id = uuid4()
            self.clients[user_id] = (reader, writer)
            await logger.info("INFO -- Hello message")
            await self.hello_message(user_id)
            await logger.info("INFO -- Compatible message")
            await self.compatible_message(user_id)
            message: BaseMessage = BaseMessage(command=self.compatible)
        except PprotoCommonException as err:
            await logger.error(err)
        while message.command != Commands.CloseConnection.value:
            message_as_dict = await self.read_message(reader)
            await logger.info("INFO -- New message")
            await logger.info(f"INFO -- Message: {str(message_as_dict)}")
            try:
                answer_response = await self.routers[UUID(message_as_dict["command"])].func(message_as_dict)
                answer = await self.make_message(answer_response, BaseMessage(**message_as_dict))
                if answer_response is not None:
                    await self.send_answer(answer, writer)
            except Exception as ex:
                if type(ex) in self.exception_handlers:
                    exception_response = await self.exception_handlers[type(ex)](message_as_dict, ex)
                    await self.send_answer(exception_response, writer)
                else:
                    traceback_text = traceback.format_exc()
                    await logger.error(f"ERROR -- {traceback_text}")
                    raise ex
        await writer.wait_closed()

    async def run(self):
        server = await asyncio.start_server(self.__handle_coroutine, self.__host, self.__port)
        addrs = ", ".join(str(sock.getsockname()) for sock in server.sockets)
        await logger.info(f"INFO -- Serving on {addrs}")
        async with server:
            await server.serve_forever()

    def include_router(self, router) -> None:
        self.routers.apeend(router)

    async def read_message(self, reader) -> BaseMessage:
        data_size = int.from_bytes(await reader.read(4), signed=True)
        data = await reader.read(abs(data_size))
        if data_size < 0:
            data = zlib.decompress(data[4:])
        as_dict = ast.literal_eval(data.decode("utf-8"))
        as_dict["flags"] = FlagMessage.parse_obj(as_dict["flags"])
        return as_dict

    async def make_message(self, answer: BaseContent, message: BaseMessage) -> BaseMessage:
        message.flags.type.value = Type.ANSWER.value
        message.flags.exec_status.value = Status.SUCCESS.value
        # TODO проверку
        message.content = answer
        return message

    async def send_answer(self, message: BaseMessage, writer: StreamWriter) -> None:
        writer.write(self.swap32_len(message=message, compress=self.use_compress))
        await writer.drain()
        if message.flags.compression.value == Compression.DISABLE.value:
            writer.write((message.model_dump_json()).encode())
        if self.use_compress:
            header = len(message.model_dump_json().encode("utf-8")).to_bytes(4, byteorder="big")
            data = zlib.compress(message.model_dump_json().encode("utf-8"))
            writer.write(header + data)
        await writer.drain()

    def add_pproto_route(
        self,
        id: UUID,
        func: Callable,
        response_model: BaseMessage = None,
    ):
        command = Command(func, response_model)
        self.routers[id] = command

    def command(
        self,
        id: UUID,
        response_model: BaseMessage = None,
    ):
        def decorator(func: Callable) -> Callable:
            self.add_pproto_route(
                id=id,
                func=func,
                response_model=response_model,
            )
            return func

        return decorator

    def event(
        self,
        id: UUID,
    ):
        def decorator(func: Callable) -> Callable:
            self.add_pproto_route(
                id=id,
                func=func,
                response_model=None,
            )
            return func

        return decorator

    def add_exception_handler(self, exc_class: Exception, handler) -> None:  # pragma: no cover
        self.exception_handlers[exc_class] = handler

    def exception_handler(self, exc_class: Exception):
        def decorator(func: Callable) -> Callable:
            self.add_exception_handler(exc_class, func)
            return func

        return decorator

    def middleware(self, middleware_type):
        pass

    def add_middleware():
        pass
