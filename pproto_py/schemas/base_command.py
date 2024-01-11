from uuid import UUID
from typing import List
from pydantic import BaseModel
from enum import Enum
from pydantic import Field


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
    id: UUID
    command: UUID
    type: Type
    execStatus: Status
    priority: Priority 
    tags: list
    maxTimeLife: int
    content: BaseModel
    compression: Compression




class BaseContent(BaseModel):

    
    async def request(kwargs) -> dict | None:
        pass
