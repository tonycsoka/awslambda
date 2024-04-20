import traceback
from collections.abc import Callable
from http import HTTPStatus

from structlog import get_logger

from ..datatypes import Response
from ..exceptions import HttpException

logger = get_logger()


class ExceptionMiddleware:
    def __init__(self, next: Callable):
        self.next = next

    def __call__(self, event, context):
        # Do stuff
        try:
            response = self.next(event, context)
        except HttpException as err:
            logger.exception("Unhandled Exception", body=err.body)
            response = Response(statusCode=err.status_code, body=err.status_code.phrase)
        except Exception:
            logger.exception("Unhandled Exception", body=traceback.format_exc())
            response = Response(
                statusCode=HTTPStatus.INTERNAL_SERVER_ERROR,
                body=HTTPStatus.INTERNAL_SERVER_ERROR.phrase,
            )

        logger.info("Status code", status_code=response.statusCode.value)
        return response
