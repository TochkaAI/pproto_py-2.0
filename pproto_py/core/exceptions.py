class PprotoCommonException(Exception):
    def __init__(self, error: str) -> None:
        super().__init__()
        self.error = error


class PProtoAnswerError(Exception):
    def __init__(self, content) -> None:
        self.content = content
        super().__init__(content)


class FailedResponseError(PProtoAnswerError):
    """Статус FAILED."""


class ErrorResponseError(PProtoAnswerError):
    """Статус ERROR."""


class UnknownResponseError(PProtoAnswerError):
    """Статус UNKNOWN."""


class FormatsException(PprotoCommonException):
    def __init__(self, error: str) -> None:
        super().__init__(error=error)
        self.error = error


class CompatibleException(PprotoCommonException):
    def __init__(self, code: int, error: str) -> None:
        super().__init__(error)


class TypeMessageError(PprotoCommonException):
    def __init__(self, error: str) -> None:
        super().__init__(error)


class PProtoMessageError(PprotoCommonException):
    ...


class PprotoConnectionError(PprotoCommonException):
    ...


class CommandTimeLifeOutError(PprotoCommonException):
    ...
