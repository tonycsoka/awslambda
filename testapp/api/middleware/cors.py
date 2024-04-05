from collections.abc import Callable

ALLOWED_ORIGINS = ["http://localhost:3001", "https://d391wccgyuzfh3.cloudfront.net"]

CORS_HEADERS = {
    "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT,PATCH,DELETE",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Credentials": "true",
}


def get_cors_headers(payload: dict) -> dict:
    """Construct CORS headers for API handler response.

    CORS headers from requests containing access credentials must specify allowed origins,
    and cannot use the "*" wildcard.
    More about the CORS policy can be found here: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#access-control-allow-origin
    """
    origin = payload["headers"]["origin"]
    if origin not in ALLOWED_ORIGINS:
        origin = ""
    return {"Access-Control-Allow-Origin": origin, **CORS_HEADERS}


class CorsMiddleware:
    def __init__(self, next: Callable):
        self.next = next

    def __call__(self, event, context):
        # Do stuff
        _headers = get_cors_headers(event)
        response = self.next(event, context)
        response["headers"] = (
            {**response["headers"], **_headers} if "headers" in response else _headers
        )
        return response
