from uuid import UUID, uuid4
from pydantic import BaseModel, Field
from enum import Enum
from typing import Any


class Type(Enum):
    COMMAND = "Command"
    ANSWER = "Answer"
    EVENT = "Event"


class Status(Enum):
    SUCCESS = "Success"
    FAILED = "Failed"
    ERROR = "Error"


class Priority(Enum):
    HIGH = "High"
    NORMAL = "Normal"
    LOW = "Low"


class Compression(Enum):
    NONE = None
    ZIP = "Zip"
    LZMA = "Lzma"
    PPMD = "Ppmd"
    DISABLE = "Disable"


class Serialize(Enum):
    JSON = "fea6b958-dafb-4f5c-b620-fe0aafbd47e2"


class BaseMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    command: UUID = Field(default_factory=uuid4) 
    type: Type = Field(default=Type.COMMAND.value)
    execStatus: Status = Field(default=Status.FAILED.value)
    priority: Priority = Field(default=Priority.NORMAL.value)
    tags: list = Field(default=[])
    maxTimeLife: int = Field(default=30)
    content: BaseModel 
    compression: Compression = Field(default=Compression.NONE.value)


class BaseContent(BaseModel):
    @classmethod
    async def format_answer(self, raw_records: dict, model: BaseModel) -> BaseModel | None:
        if not raw_records:
            return None
        return map(lambda x: model(**x), raw_records)

    # @classmethod
    # async def answer_model(self, func, model: Type[BaseModel]):
    #     async def wrapper(model: Type[BaseModel]):
    #         response = await func()
    #         return await self.format_response(response, model)

    #     return await wrapper(model)

    # async def answer(self, func):
    #     async def wrapper():
    #         return await func()

    #     return await wrapper

    # @answer
    # async def send(self, kwargs: Any) -> dict | None:
    #     return {"data": "dsaasd", "num": 1, "response": "wow"}
