import ast
import zlib
import asyncio
from uuid import UUID
from pydantic import TypeAdapter
from pydantic_core import from_json
from pproto_py.core import Formats, Commands, FormatsException
from pproto_py.schemas import BaseMessage, FlagMessage, Compression, Status
from pproto_py.base import Base


class Client(Base):

    def __init__(self,
        host="127.0.0.1",
        port=8888,
        format=Formats.JSON_PROTOCOL_FORMAT.value,
        compatible=Commands.Compatible.value,
        use_compress=False,
        compress_level: int = -1,):
        self.__host = host
        self.__port = port
        self.writer, self.reader = None, None
        self.__format = format
        self.compatible = compatible
        self.use_compress = use_compress
        self.compress_level = compress_level
    
    async def create_connect(self,) -> None:
        self.status_connect = await self.connect()


    async def hello_message(self) -> None:
        format = UUID(self.__format).bytes
        self.writer.write(format)
        await self.writer.drain()
        data = await self.reader.read(16)
        if data != format:
            raise FormatsException(error="The server format is different from the client")

    async def connect(self) -> bool:
        reader, writer = await asyncio.open_connection(self.__host, self.__port)
        self.writer = writer
        self.reader = reader
        await self.hello_message()
        await self.compatible_message()
        return True

    async def compatible_message(self) -> None:
        data_size = int.from_bytes(await self.reader.read(4))
        data_compatible = await self.reader.read(data_size)
        message = BaseMessage(
            command=self.compatible,
            maxTimeLife=5,
        )
        self.writer.write(self.swap32_len(message=message))
        await self.writer.drain()
        self.writer.write(message.model_dump_json().encode())
        await self.writer.drain()
        # TODO data_compatible checking

    @staticmethod
    async def __case_message(data: bytes, callback_func: dict) -> None:
        # as_dict = ast.literal_eval(data.decode("utf-8"))
        # TODO::Dont' use ast. JSON not equal Python dict.
        """
        ast.literal_eval:
          Safely evaluate an expression node or a Unicode or Latin-1 encoded string containing a Python expression.
          The string or node provided may only consist of the following Python literal structures:
          strings, numbers, tuples, lists, dicts, booleans, and None.

        JSON booleans != Python booleans -> false != False
        JSON null != Python None
        Please read JSON standard ECMA-404
        https://www.json.org
        """
        as_dict = from_json(data)
        as_dict["flags"] = FlagMessage.parse_obj(as_dict["flags"])
        message = TypeAdapter(BaseMessage).validate_python(as_dict)
        match message.flags.exec_status.value:
            case Status.SUCCESS.value:
                await callback_func["answer"](data)
            case Status.FAILED.value:
                await callback_func["failed"](data)
            case Status.ERROR.value:
                await callback_func["error"](data)
            case Status.UNKNOWN.value:
                await callback_func["unknown"](data)


    async def _read_with_callback(self, callback_func: dict) -> None:
        data_size = int.from_bytes(await self.reader.read(4), signed=True)
        # TODO::read(n) might return less than 'n'
        data = await self.reader.readexactly(abs(data_size))
        if data_size < 0:
            data = zlib.decompress(data[4:])
        await self.__case_message(data, callback_func)

    async def write(self, message: BaseMessage) -> None:
        # TODO переписат ьс првоеркой на use_commpress
        self.writer.write(self.swap32_len(message=message, compress=self.use_compress))
        await self.writer.drain()
        if message.flags.compression.value == Compression.DISABLE.value:
            self.writer.write((message.model_dump_json()).encode())
        if self.use_compress:
            header = len(message.model_dump_json().encode("utf-8")).to_bytes(4, byteorder="big")
            data = zlib.compress(message.model_dump_json().encode("utf-8"))
            self.writer.write(header + data)
        await self.writer.drain()

    async def write_with_callback(self, message: BaseMessage, callback_func: dict) -> None:
        self.writer.write(self.swap32_len(message=message))
        await self.writer.drain()
        if message.flags.compression.value == Compression.DISABLE.value:
            self.writer.write((message.model_dump_json()).encode())
        if message.flags.compression.value == Compression.NONE.value:
            self.writer.write(zlib.compress(message.model_dump_json().encode("utf-8")))
        await self.writer.drain()
        await self._read_with_callback(callback_func)

    async def close(self) -> None:
        self.writer.close()
        await self.writer.wait_closed()
