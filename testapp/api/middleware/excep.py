from collections.abc import Callable
from http import HTTPStatus
from ..datatypes import Response
from ..exceptions import HttpException
import sys
import traceback


def serialise_exception(exc) -> dict:
    tb = traceback.TracebackException.from_exception(exc, capture_locals=True)

    return {
        "title": type(exc).__name__,
        "message": str(exc),
        "traceback": [
            line for part in tb.format() for line in part.split("\n") if line.strip()
        ],
    }


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
            return Response(
                statusCode=HTTPStatus.BAD_REQUEST, body=serialise_exception(err)
            )
