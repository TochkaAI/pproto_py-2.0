from typing import Any, Mapping, Optional



class CommonException(Exception):
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error


class FormatsException(CommonException):
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error


class CompatibleException(CommonException):
    def __init__(self, code: int, error: str) -> None:
        super().__init__()
        self.error = error

class TypeMessageError(CommonException):
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error
