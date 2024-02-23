from uuid import UUID, uuid4
from pydantic import BaseModel, Field, model_serializer
from enum import Enum
from typing import Any, Optional
from .commands import session, Client


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
    maxTimeLife: int = Field(default=-1)
    compression: Compression = Field(default=Compression.NONE.value)
    content: BaseModel | None 


    @model_serializer()
    def serialize_model(self):
        
        if self.content is None:
            return {"id": self.id,"command": self.command,"flags": ""}
        else: 
            return {"id": self.id,"command": self.command,"flags": "", "content": self.content.model_dump_json()}


class BaseContent(BaseModel):
    
    async def send( self, 
                    server: Client,
                   **message_params) -> UUID:
        message = BaseMessage(**message_params,content=self)
        await server.write_with_callback(message,self.answer)
        return message.id
    
    
    async def answer() -> None:
        pass

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
