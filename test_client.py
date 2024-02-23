import asyncio
from uuid import UUID
from pydantic import BaseModel
from pproto_py import Client, BaseContent
from enum import Enum


class testMy(BaseContent):
    value1: int
    value2: str

    async def answer(self, data ) -> None:
        print(data)


class Commands(Enum):
    # обмен версиями
    Compatible = "173cbbeb-1d81-4e01-bf3c-5d06f9c878c3"
    # не знаем команду
    Unknown = "4aef29d6-5b1a-4323-8655-ef0d4f1bb79d"
    
    Error = "b18b98cc-b026-4bfe-8e33-e7afebfbe78b"
    
    
    CloseConnection = "e71921fd-e5b3-4f9b-8be7-283e8bb2a531"
    
    EchoConnection = "db702b07-7f5a-403f-963a-ec50d41c7305"
    # 
    JSON_PROTOCOL_FORMAT = "fea6b958-dafb-4f5c-b620-fe0aafbd47e2"


async def main():
    client =await Client.create_connect(host="127.0.0.1",port=41012)
    """
    FIXME: убрать connect() в асинхронный метод __init__() (переопределить магический метод __init__()).
    # как вариант попробовать готовую библиотеку для опредления асинхронного __init__() в любом классе
    - https://pypi.org/project/asyncinit/
    """
    
    test = testMy(value1=1, value2="lol")
    await test.send(client,command="ae2347f4-788b-4135-961c-166a3b49d65f")
    
    # base_message = BaseMessage(id=Commands.Compatible.value ,content=test)
    # await client.write(base_message)
    # await client.read()
    # await client.close()


if __name__ == "__main__":
    asyncio.run(main())