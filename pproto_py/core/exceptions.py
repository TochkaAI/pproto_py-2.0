class PprotoCommonException(Exception):
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error


class FormatsException(PprotoCommonException):
    def __init__(self, error: str) -> None:
        super().__init__(error=error)
        self.error = error


class CompatibleException(PprotoCommonException):
    def __init__(self, code: int, error: str) -> None:
        super().__init__()
        self.error = error


class TypeMessageError(PprotoCommonException):
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error
