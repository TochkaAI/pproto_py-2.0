import asyncio
import logging
import zlib
from asyncio import CancelledError
from typing import Any
from uuid import UUID

from pproto_py.base import Base
from pproto_py.client.listener import MessageReceiver
from pproto_py.client.message_pool import MessagePool
from pproto_py.core import Commands, Formats, FormatsException
from pproto_py.schemas import BaseMessage, Compression, Status
from pproto_py.client.message_dispatcher import MessageDispatcher, MessageHandler

logger = logging.getLogger(__name__)


class Client(Base):
    def __init__(
        self,
        host="127.0.0.1",
        port=8888,
        *,
        protocol_format=Formats.JSON_PROTOCOL_FORMAT.value,
        compatible=Commands.Compatible.value,
        use_compress=False,
        compress_level: int = Compression.UNDEFINED,
    ) -> None:
        self.__host = host
        self.__port = port
        self.writer, self.reader = None, None  # type: asyncio.StreamWriter | None, asyncio.StreamReader | None
        self.__protocol_format = protocol_format
        self.compatible = compatible
        self.use_compress = use_compress
        self.compress_level = compress_level
        #
        self.__message_receiver: MessageReceiver | None = None
        self.__message_pool: MessagePool | None = None
        self.__message_receiver_task: asyncio.Task | None = None
        self.__message_dispatcher: MessageDispatcher = MessageDispatcher()

    @classmethod
    async def create_connect(cls, host: str, port: int, *args: Any, **kwargs: Any) -> "Client":
        self = cls(host, port, *args, **kwargs)
        await self.connect()
        return self

    @property
    def is_connected(self) -> bool:
        return self.writer is not None

    def __str__(self):
        return f"<{self.__class__.__name__}>({self.__host}:{self.__port})"

    async def connect(self) -> bool:
        logger.debug(f"Connecting to {self}")
        reader, writer = await asyncio.open_connection(self.__host, self.__port)
        logger.debug(f"Connected {self}")
        self.writer = writer
        self.reader = reader
        # init message utils
        self.__message_receiver = MessageReceiver(reader)
        self.__message_pool = MessagePool()
        await self.hello_message()
        await self.compatible_message()
        # Start task
        self.__message_receiver_task = asyncio.create_task(
            self.__message_listener(self.__message_receiver, self.__message_pool)
        )
        return True

    async def hello_message(self) -> None:
        protocol_format = UUID(self.__protocol_format).bytes
        self.writer.write(protocol_format)
        await self.writer.drain()
        data = await self.reader.read(16)
        if data != protocol_format:
            raise FormatsException(error="The server format is different from the client")

    async def compatible_message(self) -> None:
        data_size = int.from_bytes(await self.reader.read(4))
        await self.reader.read(data_size)
        message = BaseMessage(
            command=self.compatible,
            max_time_life=5,
        )
        self.writer.write(self.swap32_len(message=message))
        await self.writer.drain()
        self.writer.write(message.model_dump_json().encode())
        await self.writer.drain()
        # TODO data_compatible checking

    @staticmethod
    async def __case_message(message: BaseMessage, callback_func: dict) -> Any:
        match message.flags.exec_status.value:
            case Status.SUCCESS.value:
                return await callback_func["answer"](message.content)
            case Status.FAILED.value:
                return await callback_func["failed"](message.content)
            case Status.ERROR.value:
                return await callback_func["error"](message.content)
            case Status.UNKNOWN.value:
                return await callback_func["unknown"](message.content)

    async def __message_listener(self, message_receiver: MessageReceiver, message_pool: MessagePool):
        # TODO::Heartbeat or pinp-pong:@cans1194
        base_commands_handlers = {
            Commands.CloseConnection.value: self.close(),
        }
        try:
            async for message in message_receiver:  # type: BaseMessage
                logger.debug(f"Received message: {message!r} on {self!r}")

                handler = base_commands_handlers.get(message.command, None)
                if handler:
                    if asyncio.iscoroutinefunction(handler):
                        await handler()
                else:
                    if message_pool.is_waiting(message.id):
                        message_pool.add_message(message)
                    else:
                        await self.__message_dispatcher.dispatch(message)
        except asyncio.CancelledError:
            logger.error(f"Connection {self!r} canceled")
            raise

    async def _read_with_callback(self, message: BaseMessage, callback_func: dict) -> None:
        received_message = await self.__message_pool.get_message(message.id, message.max_time_life)
        answer = await self.__case_message(received_message, callback_func)
        self.__message_pool.dell_message(received_message)
        return answer

    async def write(self, message: BaseMessage) -> None:
        # TODO переписат ьс првоеркой на use_commpress
        self.writer.write(self.swap32_len(message=message, compress=self.use_compress))
        await self.writer.drain()
        logger.debug(f"Write message: {message!r} on {self!r}")
        if message.flags.compression.value == Compression.DISABLE.value:
            self.writer.write((message.model_dump_json()).encode())
        if self.use_compress:
            header = len(message.model_dump_json().encode("utf-8")).to_bytes(4, byteorder="big")
            data = zlib.compress(message.model_dump_json().encode("utf-8"))
            self.writer.write(header + data)
        await self.writer.drain()

    async def write_with_callback(self, message: BaseMessage, callback_func: dict) -> None:
        # TODO:: Регистрировать id в message_pool
        self.writer.write(self.swap32_len(message=message))
        await self.writer.drain()
        logger.debug(f"Write message: {message!r} on {self!r}")
        if message.flags.compression.value == Compression.DISABLE.value:
            self.writer.write((message.model_dump_json()).encode())
        if message.flags.compression.value == Compression.NONE.value:
            self.writer.write(zlib.compress(message.model_dump_json().encode("utf-8")))
        await self.writer.drain()
        return await self._read_with_callback(message, callback_func)

    def on_message(self, command: UUID):
        def wrapper(func: MessageHandler) -> MessageHandler:
            self.__message_dispatcher.subscribe(command, func)
            return func

        return wrapper

    async def close(self) -> None:
        if self.writer is None or self.reader is None:
            logger.warning("Connection already closed.")
            return
        try:
            self.writer.close()
            self.__message_receiver_task.cancel()
            await self.writer.wait_closed()
        except (OSError, ConnectionError, CancelledError) as err:
            logger.warning(f"Error during client close: {err}")
        except Exception as err:
            logger.error(f"Unexpected error during close: {err}", exc_info=True)
        finally:
            logger.info("Client connection closed")
