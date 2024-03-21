import ast
import asyncio
from typing import Callable
from uuid import UUID
from pydantic import TypeAdapter
from pproto_py.core import Formats, Commands, FormatsException
from pproto_py.schemas import BaseMessage, FlagMessage


class Client:
    
    
    def __swap32_len(message: BaseMessage) -> int:
        message_size = len(message.model_dump_json().encode('utf-8'))
        return int.from_bytes(message_size.to_bytes(4, byteorder='little'), 
                              byteorder='big', signed=False).to_bytes(4, byteorder='little')
    
    @classmethod
    async def create_connect(self, host='127.0.0.1', port=8888,
                 format = Formats.JSON_PROTOCOL_FORMAT.value,
                 compatible = Commands.Compatible.value)  ->  "Client":
        self.__host = host
        self.__port = port
        self.__writer, self.__reader = None, None
        self.__format = format
        self.__compatible = compatible
        self.status_connect = await self.connect()
        return self
    
    @classmethod
    async def connect(self) -> bool:
        reader, writer = await asyncio.open_connection(
            self.__host,
            self.__port
        )
        self.__writer = writer
        self.__reader = reader
        await self.hello_message()
        await self.compatible_message()
        return True
    
    @classmethod
    async def compatible_message(self) -> None:
        data_size = int.from_bytes(await self.__reader.read(4))        
        data_compatible = await self.__reader.read(data_size)
        message = BaseMessage(command=self.__compatible,
                              maxTimeLife=5,)
        self.__writer.write(self.__swap32_len(message=message))
        await self.__writer.drain() 
        self.__writer.write(message.model_dump_json().encode())
        await self.__writer.drain()
        # TODO data_compatible checking
    
    
    @classmethod
    async def hello_message(self) -> None:
        format = UUID(self.__format).bytes
        self.__writer.write(format)
        await self.__writer.drain()
        data = await self.__reader.read(16)
        if data != format:
            raise FormatsException(error="The server format is different from the client")
    
    async def __case_message(data: bytes, callback_func: Callable) -> None:
        as_dict = ast.literal_eval(data.decode('utf-8'))
        as_dict["flags"] = FlagMessage.parse_obj(as_dict["flags"])
        message = TypeAdapter(BaseMessage).validate_python(as_dict)
        # TODO case message
        await callback_func(data)
        pass
    
    
    @classmethod
    async def _read_with_callback(self, callback_func: Callable) -> None:
        data_size = int.from_bytes(await self.__reader.read(4))
        data = await self.__reader.read(data_size)
        self.__case_message(data,callback_func)

    
    async def write(self, message: BaseMessage) -> None:
        self.__writer.write(self.__swap32_len(message))
        await self.__writer.drain()
        self.__writer.write((message.model_dump_json()).encode())
        await self.__writer.drain()
    
    
    @classmethod
    async def write_with_callback(self, message: BaseMessage, callback_func: Callable) -> None:
        self.__writer.write(self.__swap32_len(message))
        await self.__writer.drain()
        self.__writer.write((message.model_dump_json()).encode())
        await self.__writer.drain()
        await self._read_with_callback(callback_func)


    @classmethod
    async def close(self) -> None:
        self.__writer.close()
        await self.__writer.wait_closed()
    
