import zlib

from pproto_py.schemas import BaseMessage


class Base:
    @staticmethod
    def __swap32_len(message_size: int) -> bytes:
        return int.from_bytes(
            message_size.to_bytes(4, byteorder="little", signed=True), byteorder="big", signed=False
        ).to_bytes(4, byteorder="little")

    @staticmethod
    def swap32_bytes_len(data: bytes, compress: bool = False) -> bytes:
        if compress:
            message_size = len(data) * -1
        else:
            message_size = len(data)
        return Base.__swap32_len(message_size)

    @staticmethod
    def swap32_len(message: BaseMessage, compress: bool = False) -> bytes:
        if compress:
            return Base.swap32_bytes_len(zlib.compress(message.model_dump_json().encode("utf-8")), compress)
        else:
            return Base.swap32_bytes_len(message.model_dump_json().encode("utf-8"), compress)
