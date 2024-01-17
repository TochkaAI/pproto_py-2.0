import asyncio
from pproto_py.schemas import BaseMessage


class Client:
    def __init__(self, host='127.0.0.1', port=8888) -> None:
        self.__host = host
        self.__port = port
        self.__writer, self.__reader = None, None
    
    async def connect(self):
        reader, writer = await asyncio.open_connection(
            self.__host,
            self.__port
        )
        self.__writer = writer
        self.__reader = reader
    
    async def read(self):
        data = await self.__reader.read(100)
        print(f'Received: {data.decode()!r}')
        
    async def write(self, message: BaseMessage):
        self.__writer.write((message.model_dump_json()).encode())
        await self.__writer.drain()
        self.__writer.close()
        await self.__writer.wait_closed()
        
    
async def main():
    client = Client()
    """
    FIXME: убрать connect() в асинхронный метод __init__() (переопределить магический метод __init__()).
    # как вариант попробовать готовую библиотеку для опредления асинхронного __init__() в любом классе
    - https://pypi.org/project/asyncinit/
    """
    await client.connect()
    base_message = BaseMessage()
    await client.write(base_message)


if __name__ == "__main__":
    asyncio.run(main())
