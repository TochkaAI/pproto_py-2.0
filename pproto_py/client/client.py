import asyncio
import logging
import random
import zlib
from asyncio import CancelledError
from typing import Any, Callable, Awaitable
from uuid import UUID

from pproto_py.base import Base
from pproto_py.client.listener import MessageReceiver
from pproto_py.client.message_dispatcher import MessageDispatcher, MessageHandler
from pproto_py.client.message_pool import MessagePool
from pproto_py.core import Commands, Formats, FormatsException
from pproto_py.core.exceptions import ErrorResponseError, CommandTimeLifeOutError
from pproto_py.schemas import BaseMessage, Compression, Status

logger = logging.getLogger(__name__)


class Client(Base):
    def __init__(
        self,
        host="127.0.0.1",
        port: int = 8888,
        *,
        protocol_format: Formats = Formats.JSON_PROTOCOL_FORMAT.value,
        compatible=Commands.Compatible.value,
        use_compress=False,
        compress_level: int = Compression.UNDEFINED,
        reconnect_attempts: int | None = None,
        reconnect_delay: int = 1,
        reconnect_max_delay: int = 30,
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
        self.__heartbeat_task: asyncio.Task | None = None
        self.__message_dispatcher: MessageDispatcher = MessageDispatcher()
        self.connected: asyncio.Event = asyncio.Event()
        self._heartbeat_timeout: int = 30
        #
        self._closing: bool = False
        self._reconnect_lock: asyncio.Lock = asyncio.Lock()
        self._reconnect_attempts: int | None = reconnect_attempts
        self._reconnect_delay: int = reconnect_delay
        self._reconnect_max_delay: int = reconnect_max_delay
        #
        self._on_reconnect_callbacks: list[Callable[[], Awaitable[None]]] = []
        self._on_disconnect_callbacks: list[Callable[[], Awaitable[None]]] = []

    @classmethod
    async def create_connect(cls, host: str, port: int, *args: Any, **kwargs: Any) -> "Client":
        self = cls(host, port, *args, **kwargs)
        await self.connect()
        return self

    @property
    def is_connected(self) -> bool:
        return (
            self.writer is not None
            and self.__message_receiver_task is not None
            and not self.__message_receiver_task.done()
        )

    def add_reconnect_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_reconnect_callbacks.append(callback)

    def add_disconnect_callback(self, callback: Callable[[], Awaitable[None]]) -> None:
        self._on_disconnect_callbacks.append(callback)

    def __str__(self) -> str:
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

    async def echo_connection_heartbeat(self) -> None:
        heartbeat_msg = BaseMessage(command=Commands.EchoConnection.value, content=None, max_time_life=-1)

        async def answer(content):
            return content

        callbacks = {
            "answer": answer,
            "error": lambda msg: (_ for _ in ()).throw(ErrorResponseError(msg)),
        }
        while self.connected.is_set():
            await asyncio.sleep(self._heartbeat_timeout)
            if not self.connected.is_set():
                return
            try:
                await asyncio.wait_for(
                    self.write_with_callback(heartbeat_msg, callbacks),
                    timeout=self._heartbeat_timeout * 2,
                )
            except ErrorResponseError as err:
                logger.error(f"Error during heartbeat: {err}")
            except (asyncio.TimeoutError, CommandTimeLifeOutError):
                logger.error(f"Heartbeat timeout on {self!r}, reconnecting...")
                asyncio.create_task(self.__handle_disconnect())
                return

    async def _cleanup_connection(self) -> None:
        self.connected.clear()
        if self.__heartbeat_task and not self.__heartbeat_task.done():
            self.__heartbeat_task.cancel()
        if self.__message_receiver_task and not self.__message_receiver_task.done():
            self.__message_receiver_task.cancel()
        if self.__message_pool is not None:
            self.__message_pool.fail_all(ConnectionError("Connection lost, reconnecting..."))
        if self.writer is not None:
            self.writer.close()
            try:
                await self.writer.wait_closed()
            except Exception:  # noqa: BLE001
                pass
        self.writer, self.reader = None, None

    async def _reconnect(self) -> None:
        attempt = 0
        delay = self._reconnect_delay
        while True:
            attempt += 1
            if self._reconnect_attempts is not None and attempt > self._reconnect_attempts:
                raise ConnectionError(f"Failed to reconnect to {self!r} after {attempt} attempts")
            try:
                logger.debug(f"Trying to reconnect to {self!r} (attempt {attempt})")
                await self.connect()
                for cb in self._on_reconnect_callbacks:
                    asyncio.create_task(cb())
                logger.info(f"Reconnected to {self!r} after {attempt} attempts")
                return
            except (OSError, ConnectionError, FormatsException):
                logger.warning(f"Reconnect to {self!r} failed (attempt {attempt})")
                await asyncio.sleep(delay + random.uniform(0, delay * 0.1))
                delay = min(delay * 2, self._reconnect_max_delay)

    async def __handle_echo_connection(self) -> None:
        ...

    async def __handle_close_connection(self) -> None:
        ...

    async def __handle_disconnect(self) -> None:
        if self._closing:
            return
        if self._reconnect_lock.locked():
            logger.debug(f"Reconnect already in progress for {self!r}")
            return
        async with self._reconnect_lock:
            logger.warning(f"Connection lost on {self!r}, starting reconnect")
            await self._cleanup_connection()
            try:
                await self._reconnect()
            except ConnectionError as err:
                logger.error(f"Giving up on {self!r}: {err}")
                raise

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

    async def __message_listener(self, message_receiver: MessageReceiver, message_pool: MessagePool) -> None:
        self.connected.set()
        base_commands_handlers = {
            Commands.CloseConnection.value: self.close,
            Commands.EchoConnection.value: self.__handle_echo_connection,
        }
        self.__heartbeat_task = asyncio.create_task(self.echo_connection_heartbeat())
        try:
            async for message in message_receiver:  # type: BaseMessage
                logger.debug(f"Received message: {message!r} on {self!r}")  # noqa: G004

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
        except (ConnectionError, OSError) as err:
            logger.error(f"Connection {self!r} lost: {err}")
            if not self._closing:
                asyncio.create_task(self._handle_disconnect())

    async def _read_with_message_response(self, message: BaseMessage) -> BaseMessage:
        received_message = await self.__message_pool.get_message(message.id, message.max_time_life)
        self.__message_pool.dell_message(received_message)
        return received_message

    async def _read_with_callback(self, message: BaseMessage, callback_func: dict) -> tuple[BaseMessage, Any | None]:
        received_message = await self.__message_pool.get_message(message.id, message.max_time_life)
        answer = await self.__case_message(received_message, callback_func)
        self.__message_pool.dell_message(received_message)
        return received_message, answer

    async def write(self, message: BaseMessage) -> None:
        # FIXME::Добавить опцию на сжатие только контента
        if self.use_compress:
            data_bytes = zlib.compress(message.model_dump_json().encode("utf-8"))
        else:
            data_bytes = message.model_dump_json().encode()
        self.writer.write(
            self.swap32_bytes_len(
                data=data_bytes,
                compress=self.use_compress,
            )
        )
        await self.writer.drain()
        self.writer.write(data_bytes)
        logger.debug(f"Write message: {message!r} on {self!r}")
        await self.writer.drain()

    async def write_with_callback(self, message: BaseMessage, callback_func: dict) -> None:
        self.__message_pool.register_wait(message.id)
        await self.write(message)
        message, answer = await self._read_with_callback(message, callback_func)
        return answer

    async def with_message_response(self, message: BaseMessage) -> BaseMessage:
        self.__message_pool.register_wait(message.id)
        await self.write(message)
        return await self._read_with_message_response(message)

    def on_message(self, command: UUID):
        def wrapper(func: MessageHandler) -> MessageHandler:
            self.__message_dispatcher.subscribe(command, func)
            return func

        return wrapper

    async def close(self) -> None:
        self._closing = True
        self.connected.clear()
        if self.writer is None or self.reader is None:
            logger.warning("Connection already closed.")
            return
        try:
            if self.__heartbeat_task and not self.__heartbeat_task.done():
                self.__heartbeat_task.cancel()
            self.writer.close()
            if self.__message_receiver_task and not self.__message_receiver_task.done():
                self.__message_receiver_task.cancel()
            await self.writer.wait_closed()
        except (OSError, ConnectionError, CancelledError) as err:
            logger.warning(f"Error during client close: {err}")
        except Exception as err:
            logger.error(f"Unexpected error during close: {err}", exc_info=True)
        finally:
            self.writer, self.reader = None, None
            logger.info("Client connection closed")
