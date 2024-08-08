from uuid import UUID
from pydantic import BaseModel


class BasePprotoErrorContent(BaseModel):
    group: int
    code: UUID
    description: str
