from pydantic import BaseModel
from .multipart import MultipartDecoder
from http import HTTPStatus
from typing import Any

class Context:
    data: Any

    def __init__(self, body: Any):
        self.data = body


class Response(BaseModel):
    statusCode:HTTPStatus = HTTPStatus.OK
    headers:dict[Any,Any] = {
        "content-type": "application/json"
    }
    body:Any = None
    isBase64Encoded:bool = False


class Request:
    data: dict

    def __init__(self, body: dict):
        self.data = body


class Body(Any):
    pass


class Headers(dict):
    pass


class File:
    headers: Headers
    content: str

    def __init__(self, content: str, headers: Headers):
        self.content = content
        self.headers = headers
        self.extract_file()

    def extract_file(self):
        content_type = self.headers["Content-Type"]

        multipart_data = MultipartDecoder(self.content, content_type)

        filename = None
        part = multipart_data.parts[0]
        content = part.content
        disposition = part.headers[b"Content-Disposition"]
        for content_info in str(disposition).split(";"):
            info = content_info.split("=", 2)
            if info[0].strip() == "filename":
                filename = info[1].strip("\"'\t \r\n")
        assert filename is not None
        self.filename = filename
        self.file = content
