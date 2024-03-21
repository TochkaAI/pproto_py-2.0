import ast
from pproto_py.client import Client
from pydantic import BaseModel, TypeAdapter


def session(func):
    session = Client()

    def wrapper(*args, **kwargs):
        return func(*args, session, **kwargs)

    return wrapper


async def format_answer(raw_records: dict, model: BaseModel) -> BaseModel | None:
    if not raw_records:
        return None
    return map(lambda x: model(**x), raw_records)


def to_model(model: BaseModel):
    def outher(func):
        async def inner(*args, **kwargs):
            as_str = ast.literal_eval(args[1].decode("utf-8"))
            data: BaseModel = TypeAdapter(model).validate_python(as_str["content"])
            if len(args[2:]) != 0:
                new_args = (args[0], data, args[2:])
            else:
                new_args = (args[0], data)
            res = await func(*new_args, **kwargs)
            return res

        return inner

    return outher
