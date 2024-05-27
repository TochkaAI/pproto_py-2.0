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
