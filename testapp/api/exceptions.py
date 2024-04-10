from http import HTTPStatus
from typing import Any


class HttpException(Exception):
    status_code: HTTPStatus
    body: Any

    def __init__(self, status_code=HTTPStatus.INTERNAL_SERVER_ERROR, body=None):
        self.status_code = status_code
        self.body = body
        super().__init__(body)
