from pproto_py import BaseContent, BaseMessage
from uuid import UUID
from pydantic import Field, BaseModel
from enum import Enum

class Commands(Enum):
	Compatible      = '173cbbeb-1d81-4e01-bf3c-5d06f9c878c3'
	Unknown         = '4aef29d6-5b1a-4323-8655-ef0d4f1bb79d'
	Error           = 'b18b98cc-b026-4bfe-8e33-e7afebfbe78b'
	CloseConnection = 'e71921fd-e5b3-4f9b-8be7-283e8bb2a531'
	EchoConnection  = 'db702b07-7f5a-403f-963a-ec50d41c7305'


class MyContent(BaseContent):
    data: str
    num: int


class MyContent2(BaseContent):
    data: str
    num: int
    rew: str


class MyCommand1(MyContent):
    command: UUID = Field(default=Commands.Compatible.value)
    
class MyCommand2(MyContent):
    command: UUID = Field(default=Commands.Unknown.value)
    

class AnswerFastAPi(BaseModel):
    data: str
    num: int
    helo: list


test_content = MyCommand2(data="[eq]",num=1)
# {data:"[eq]",num:1 ,command: "Dsasadasd"}

answer : AnswerFastAPi = await test_content.request()
