from collections.abc import Callable
from http import HTTPStatus
from ..datatypes import Response

def is_authorized(event):
    return True;

class AuthMiddleware:
    def __init__(self, next: Callable):
        self.next = next

    def __call__(self, event, context):
        if not is_authorized(event):
            return Response(statusCode=HTTPStatus.UNAUTHORIZED, body="Unauthorized request")
        response = self.next(event, context)
        # Do more stuff
        return response
