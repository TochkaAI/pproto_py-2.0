from pproto_py.client import Client
from pydantic import BaseModel
import ast


def session(func):
    session = Client()
    def wrapper(*args, **kwargs):
        return func(*args,session, **kwargs)
    return wrapper

async def format_answer(self, raw_records: dict, model: BaseModel) -> BaseModel | None:
        if not raw_records:
            return None
        return map(lambda x: model(**x), raw_records)


def to_model(model: BaseModel):
    def outher(func):
        def inner(*args, **kwargs):
            res = func(*args, **kwargs)
            as_str = ast.literal_eval(res.decode('utf-8'))
            return map(lambda x: model(**x), as_str)
        return inner
    return outher
