from enum import Enum
from typing import Annotated
from uuid import UUID, uuid4

from pydantic_core import from_json
from pydantic import BaseModel, Field, model_serializer, PlainSerializer, ConfigDict, TypeAdapter
from pydantic.alias_generators import to_camel


class Type(Enum):
    UNKNOWN = 0
    COMMAND = 1
    ANSWER = 2
    EVENT = 3


class Status(Enum):
    UNKNOWN = 0
    SUCCESS = 1
    FAILED = 2
    ERROR = 3


class Priority(Enum):
    HIGH = 0
    NORMAL = 1
    LOW = 2


class Compression(Enum):
    UNDEFINED = -1
    NONE = 0
    ZIP = 1
    LZMA = 2
    PPMD = 3
    DISABLE = 7


class SerializationFormat:
    BProto = 0  # Бинарный формат
    Json = 1  # Json формат
    # LastFormat = 7 Предполагается, что будет не больше 8 форматов


def int2bit(x: int, size: int):
    """
    Перевод в int в фиксированные 4 байта
    """
    return bin(x)[2:].zfill(size)


class FlagField(BaseModel):
    name: str = Field(...)
    value: int
    size: int

    @model_serializer()
    def serialize_model(self):
        return int2bit(self.value, self.size)


ByteField = Annotated[FlagField, PlainSerializer(lambda x: int2bit(x.value))]


class FlagMessage(BaseModel):
    # 1 Байт
    type: ByteField = ByteField(name="Type", value=Type.COMMAND.value, size=3)
    exec_status: ByteField = ByteField(name="ExecStatus", value=Status.UNKNOWN.value, size=3)
    priority: ByteField = ByteField(name="priority", value=Priority.NORMAL.value, size=2)
    # 2 Байт
    compression: ByteField = ByteField(name="compression", value=Compression.DISABLE.value, size=3)
    tags_is_empty: ByteField = ByteField(name="tagsIsEmpty", value=0, size=1)
    max_time_life_is_empty: ByteField = ByteField(name="maxTimeLife", value=0, size=1)
    content_is_empty: ByteField = ByteField(name="contentIsEmpty", value=1, size=1)
    reserved_2: ByteField = ByteField(name="reserved2", value=0, size=2)
    # 3 Байт
    reserved_3: ByteField = ByteField(name="reserved3", value=0, size=8)
    # 4 Байт
    content_format: ByteField = ByteField(name="contentFormat", value=SerializationFormat.Json, size=3)
    reserved_4: ByteField = ByteField(name="reserved4", value=0, size=4)
    flags_2_is_empty: ByteField = ByteField(name="flags2IsEmpty", value=0, size=1)

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @model_serializer()
    def serialize_model(self) -> int:
        res = ""
        for k in reversed(self.model_fields.keys()):
            res += getattr(self, k).model_dump()
        return int(res, 2)

    @classmethod
    def parse_obj(cls, flags: int) -> "FlagMessage":
        b_string = bin(flags)[2:].zfill(8 * 4)
        flag = FlagMessage()
        for f in reversed(cls.model_fields.keys()):
            f_field: FlagField = getattr(flag, f)
            f_field.value = int(b_string[0 : f_field.size], 2)
            b_string = b_string[f_field.size :]
        return flag


class Serialize(Enum):
    JSON = "fea6b958-dafb-4f5c-b620-fe0aafbd47e2"


class BaseMessage(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    command: UUID
    flags: FlagMessage = Field(..., default_factory=FlagMessage)
    tags: list = None
    content: BaseModel | dict | None = None
    max_time_life: int = 30

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    @model_serializer()
    def serialize_model(self):
        if self.content is None:
            return {
                "id": self.id,
                "command": self.command,
                "flags": self.flags.model_dump(),
                "maxTimeLife": self.max_time_life,
            }
        else:
            return {
                "id": self.id,
                "command": self.command,
                "flags": self.flags.model_dump(),
                "content": self.content.model_dump(),
                "maxTimeLife": self.max_time_life,
            }

    @classmethod
    def from_json(cls, json: str | bytes | bytearray) -> "BaseMessage":
        # as_dict = ast.literal_eval(data.decode("utf-8"))
        # TODO::Dont' use ast. JSON not equal Python dict.
        """
        ast.literal_eval:
          Safely evaluate an expression node or a Unicode or Latin-1 encoded string containing a Python expression.
          The string or node provided may only consist of the following Python literal structures:
          strings, numbers, tuples, lists, dicts, booleans, and None.

        JSON booleans != Python booleans -> false != False
        JSON null != Python None
        Please read JSON standard ECMA-404
        https://www.json.org
        """
        json_dict = from_json(json)
        json_dict["flags"] = FlagMessage.parse_obj(json_dict["flags"])
        message = TypeAdapter(BaseMessage).validate_python(json_dict)  # type: ignore
        message.content = json_dict["content"]
        return message
