from enum import Enum


class Commands(Enum):
    Compatible = "173cbbeb-1d81-4e01-bf3c-5d06f9c878c3"
    Unknown = "4aef29d6-5b1a-4323-8655-ef0d4f1bb79d"
    Error = "b18b98cc-b026-4bfe-8e33-e7afebfbe78b"
    CloseConnection = "e71921fd-e5b3-4f9b-8be7-283e8bb2a531"
    EchoConnection = "db702b07-7f5a-403f-963a-ec50d41c7305"


class Formats(Enum):
    JSON_PROTOCOL_FORMAT = "fea6b958-dafb-4f5c-b620-fe0aafbd47e2"
