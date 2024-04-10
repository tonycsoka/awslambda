from collections.abc import Callable
from http import HTTPStatus

from structlog import get_logger

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
            logger = get_logger()
            logger.exception("Unhandled Exception")
            return Response(
                statusCode=HTTPStatus.INTERNAL_SERVER_ERROR, body=err.__str__()
            )
