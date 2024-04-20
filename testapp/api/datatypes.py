from http import HTTPStatus
from typing import Any

from pydantic import BaseModel

from .aws.awsevent import EventV1


class Context:
    data: Any

    def __init__(self, data: Any):
        self.data = data


class Response(BaseModel):
    statusCode: HTTPStatus = HTTPStatus.OK
    headers: dict[Any, Any] = {"content-type": "application/json"}
    body: Any = None
    isBase64Encoded: bool = False


class Event(BaseModel):
    event: EventV1


class Body:
    data: Any

    def __init__(self, data: Any):
        self.data = data


class Headers(dict):
    pass


class File(BaseModel):
    filename: str
