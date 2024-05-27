import asyncio
from pproto_py import BaseContent
from uuid import UUID
from pydantic import Field, BaseModel
from enum import Enum


class Commands(Enum):
    Compatible = "173cbbeb-1d81-4e01-bf3c-5d06f9c878c3"
    Unknown = "4aef29d6-5b1a-4323-8655-ef0d4f1bb79d"
    Error = "b18b98cc-b026-4bfe-8e33-e7afebfbe78b"
    CloseConnection = "e71921fd-e5b3-4f9b-8be7-283e8bb2a531"
    EchoConnection = "db702b07-7f5a-403f-963a-ec50d41c7305"


class MyAnswer(BaseModel):
    data: str
    num: int
    response: str


class MyContent(BaseContent):
    data: str
    num: int

    @BaseContent.answer_model(MyAnswer)
    async def response(self, func):
        async def wrapper():
            return await func()

        return await wrapper


class MyCommand(MyContent):
    command: UUID = Field(default=Commands.Compatible.value)


async def main():
    test_content = MyCommand(data="[eq]", num=1)
    # {data:"[eq]",num:1 ,command: "Dsasadasd"}

    answer: MyAnswer = await test_content.send_with_answer()

    answer = await test_content.give_me_answer()


loop = asyncio.get_event_loop()
loop.run_until_complete(main)
