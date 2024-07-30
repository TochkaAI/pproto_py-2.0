import ast
from pproto_py.client import Client
from pydantic import BaseModel, TypeAdapter
from pydantic_core import from_json


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
            # as_str = ast.literal_eval(args[1].decode("utf-8"))
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
            as_dict = from_json(args[1])
            data: BaseModel = TypeAdapter(model).validate_python(as_dict["content"])
            if len(args[2:]) != 0:
                new_args = (args[0], data, args[2:])
            else:
                new_args = (args[0], data)
            res = await func(*new_args, **kwargs)
            return res

        return inner

    return outher
