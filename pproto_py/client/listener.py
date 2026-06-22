import asyncio
import zlib
from collections.abc import AsyncIterable

from pproto_py.core.exceptions import PprotoConnectionError, PProtoMessageError
from pproto_py.schemas import BaseMessage


def bytes_to_human_readable(num: int, suffix="B") -> str:
    for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
        if abs(num) < 1024.0:
            return f"{num:3.1f}{unit}{suffix}"
        num /= 1024.0
    return f"{num:.1f}Yi{suffix}"


class MessageReceiver(AsyncIterable):
    def __init__(self, reader: asyncio.StreamReader) -> None:
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
                # Receive b'\x00\x00'
                if not data:
                    raise PProtoMessageError("Empty message")
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
