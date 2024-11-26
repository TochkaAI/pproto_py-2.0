import asyncio
import zlib
from collections.abc import AsyncIterable

from pproto_py.schemas import BaseMessage
from pproto_py.core.exceptions import PprotoConnectionError


class MessageReceiver(AsyncIterable):
    def __init__(self, reader: asyncio.StreamReader):
        self.reader = reader
        self.lock = asyncio.Lock()

    def __aiter__(self) -> "MessageReceiver":
        return self

    async def __anext__(self) -> BaseMessage:
        return await self.get_message()

    async def get_message(self) -> BaseMessage:
        async with self.lock:
            if self.reader is None:
                raise PprotoConnectionError("Connection closed")
            try:
                data_size = int.from_bytes(await self.reader.read(4), signed=True)
                data = await self.reader.readexactly(abs(data_size))
                if data_size < 0:
                    data = zlib.decompress(data[4:])
                message = BaseMessage.from_json(data)
            except asyncio.IncompleteReadError as err:
                raise PprotoConnectionError("") from err
            except ConnectionRefusedError as err:
                raise PprotoConnectionError("") from err
            except ConnectionResetError as err:
                raise PprotoConnectionError("") from err
            except ConnectionError as err:
                raise PprotoConnectionError("") from err
            except OSError as err:
                raise PprotoConnectionError(f"Communication error: {err!r}") from err
        return message
