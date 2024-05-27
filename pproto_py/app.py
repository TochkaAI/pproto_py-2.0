from typing import TypeVar
from server import Server
from client import Client

AppType = TypeVar("AppType", bound="PProto")


class PProto:
    def ___init__(
        self: AppType, connection_host: str, connection_port: int, self_host: str, self_port: int
    ) -> "PProto":
        self.__server = Server(self_host, self_port)
        self.__client = Client(connection_host, connection_port)

    def inlucde_router():
        pass
