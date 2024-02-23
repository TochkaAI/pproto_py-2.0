from typing import Any, Mapping, Optional



class CommonException(Exception):
    def __init__(self, code: int, error: str) -> None:
        super().__init__()
        self.error = error
        self.code = code


class FormatsException(Exception):
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error


class CompatibleException(Exception):
    def __init__(self, code: int, error: str) -> None:
        super().__init__()
        self.error = error
        self.code = code

