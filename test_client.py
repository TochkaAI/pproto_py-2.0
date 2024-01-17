import asyncio
from pydantic import BaseModel
from pproto_py.client import Client
from pproto_py.schemas import BaseMessage

class testMy(BaseModel):
    dsa: str
    dsa2: int


async def main():
    client = Client()
    """
    FIXME: убрать connect() в асинхронный метод __init__() (переопределить магический метод __init__()).
    # как вариант попробовать готовую библиотеку для опредления асинхронного __init__() в любом классе
    - https://pypi.org/project/asyncinit/
    """
    await client.connect()
    test = testMy(dsa="dsa",dsa2=2)
    base_message = BaseMessage(content=test)
    await client.write(base_message)


if __name__ == "__main__":
    asyncio.run(main())