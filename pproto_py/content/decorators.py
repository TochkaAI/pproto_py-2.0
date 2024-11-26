from typing import TypeVar, Type

from pydantic import BaseModel, TypeAdapter

from pproto_py.client import Client
from pproto_py.content import BaseContent


ModelType = TypeVar("ModelType", bound=BaseModel)
ContentType = TypeVar("ContentType", bound=BaseContent)


def session(func):
    session = Client()

    def wrapper(*args, **kwargs):
        return func(*args, session, **kwargs)

    return wrapper


async def format_answer(raw_records: dict, model: BaseModel) -> BaseModel | None:
    if not raw_records:
        return None
    return map(lambda x: model(**x), raw_records)


def to_model(model: Type[ModelType | ContentType]):
    def outer(func):
        async def inner(*args, **kwargs):
            content_model: BaseModel = TypeAdapter(model).validate_python(args[1])
            if len(args[2:]) != 0:
                new_args = (args[0], content_model, args[2:])
            else:
                new_args = (args[0], content_model)
            res = await func(*new_args, **kwargs)
            return res

        return inner

    return outer
