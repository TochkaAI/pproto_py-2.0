import asyncio


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
        
    async def write(self, message):
        self.__writer.write(message.encode())
        await self.__writer.drain()
        self.__writer.close()
        await self.__writer.wait_closed()
        
    
async def main():
    client = Client()
    await client.connect()
    await client.write('test string')


if __name__ == "__main__":
    asyncio.run(main())
