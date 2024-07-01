from typing import Callable, Optional, Dict
from uuid import UUID
from pproto_py.content import BaseContent
from pproto_py.schemas import BaseMessage


class Router:
    def __init__(
        self,
    ) -> None:
        self.routers: Dict[UUID, Command] = {}

    async def event(id: UUID, **kawrgs):
        pass

    async def command(id: UUID, response_model: BaseContent, **kwargs):
        pass


class Command:
    def __init__(
        self,
        func: Callable,
        response_model=Optional[BaseContent | BaseMessage],
    ):
        self.func = func
        self.response_model = response_model
