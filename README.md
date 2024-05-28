pproto-py 2.0


### Example Client

```Python
import asyncio
from uuid import UUID
from pproto_py import Client, BaseContent, to_model, BasePprotoErrorContent
from uuid import uuid4, UUID


class testMy(BaseContent):
    value1: int
    value2: str

    async def answer(self, data) -> None:
        print(data)


class testMy2(BaseContent):
    value1: int
    value2: UUID

    @to_model(testMy)
    async def answer(self, data: testMy) -> None:
        print(data.model_dump_json())

    @to_model(BasePprotoErrorContent)
    async def error(self, data: BasePprotoErrorContent) -> None:
        print(data.model_dump_json())


async def main():
    client = await Client.create_connect(host="127.0.0.1", port=8888)

    test2 = testMy2(value1=10, value2=uuid4())
    test_id2 = await test2.send(client, command="114949cb-2b6a-48f4-a5a4-15a682b2f45a")
    print("dsa")


if __name__ == "__main__":
    asyncio.run(main())
```
### Example Server
```Python
import asyncio
from typing import Dict
from uuid import UUID
from pproto_py import Pproto
from pproto_py import BaseContent, BaseMessage, Status, BasePprotoErrorContent


class CommonException(Exception):
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error


class testMy(BaseContent):
    value1: int
    value2: str


server = Pproto()


@server.exception_handler(CommonException)
async def common_exception(message: Dict[str,str], exc: CommonException):
    print(exc.error)
    message_error = BaseMessage(command=message.command)
    message_error.flags.exec_status.value = Status.ERROR.value
    message_error.content = BasePprotoErrorContent(error=exc.error)
    return message_error


@server.command(id=UUID("114949cb-2b6a-48f4-a5a4-15a682b2f45a"),
                response_model=testMy)
async def example1(content):
    # raise CommonException(error="Фигня какая-то")
    dsa = testMy(value1=1,value2="dsa")
    return dsa


async def main():
    await server.run()


if __name__ == "__main__":
    asyncio.run(main())
```
