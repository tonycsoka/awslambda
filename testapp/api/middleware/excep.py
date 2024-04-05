from collections.abc import Callable
from http import HTTPStatus


class ExceptionMiddleware:
    def __init__(self, next: Callable):
        self.next = next

    def __call__(self, event, context):
        # Do stuff
        try:
            response = self.next(event, context)
            return response
        except Exception as err:
            return {
                "isBase64Encoded": False,
                "statusCode": HTTPStatus.BAD_REQUEST,
                "body": err,
            }
