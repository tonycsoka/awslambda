from collections.abc import Callable

CORS_HEADERS = {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT,PATCH,DELETE",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
}


class CorsMiddleware:
    def __init__(self, next: Callable):
        self.next = next

    def __call__(self, event, context):
        # Do stuff
        response = self.next(event, context)
        response["headers"] = (
            {**response["headers"], **CORS_HEADERS}
            if "headers" in response
            else CORS_HEADERS
        )
        return response
