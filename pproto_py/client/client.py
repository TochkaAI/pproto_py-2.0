import asyncio
from typing import Callable
from uuid import UUID
from pydantic import BaseModel
from pproto_py.core import Formats, Commands, FormatsException


class Client:
    
    
    # TODO key - id message, value - object ??? - callback
    
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
        compatible = UUID(self.__compatible).bytes
        self.__writer.write(compatible)
        await self.__writer.drain()
        # if data_compatible != compatible:
        #     raise FormatsException(error="The server compatible is different from the client")    
    
    @classmethod
    async def hello_message(self) -> None:
        format = UUID(self.__format).bytes
        self.__writer.write(format)
        await self.__writer.drain()
        data = await self.__reader.read(16)
        if data != format:
            raise FormatsException(error="The server format is different from the client")
    
    @classmethod
    async def _read_with_callback(self,callback_func: Callable):
        data_size = int.from_bytes(await self.__reader.read(4))
        data = await self.__reader.read(data_size)
        await callback_func(data)
        
    
    @classmethod
    async def write_with_callback(self, message: BaseModel, callback_func: Callable):
        self.__writer.write(len(message.model_dump_json().encode('utf-8')).to_bytes(4, 'little')) # размер объекта в байтах
        await self.__writer.drain()
        self.__writer.write((message.model_dump_json()).encode())
        await self.__writer.drain()
        await self._read_with_callback(callback_func)


    @classmethod
    async def close(self):
        self.__writer.close()
        await self.__writer.wait_closed()
    
    
    async def __get_answer(self, id : UUID) :
        return self.__client_history[id]
