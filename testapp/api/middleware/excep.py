from collections.abc import Callable
from http import HTTPStatus
from ..datatypes import Response
from ..exceptions import HttpException


class ExceptionMiddleware:
    def __init__(self, next: Callable):
        self.next = next

    def __call__(self, event, context):
        # Do stuff
        try:
            response = self.next(event, context)
            return response
        except HttpException as err:
            return Response(statusCode=err.status_code, body=err.body)
        except Exception as err:
            return Response(statusCode=HTTPStatus.BAD_REQUEST, body=err.__str__())
