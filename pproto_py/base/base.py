import zlib
from pproto_py.schemas import BaseMessage


class Base:
    @staticmethod
    def swap32_len(message: BaseMessage, compress: bool = False) -> int:
        if compress:
            message_size = len(zlib.compress(message.model_dump_json().encode("utf-8"))) * -1
        else:
            message_size = len(message.model_dump_json().encode("utf-8"))
        bytes_size = int.from_bytes(
            message_size.to_bytes(4, byteorder="little", signed=True), byteorder="big", signed=False
        ).to_bytes(4, byteorder="little")
        return bytes_size
