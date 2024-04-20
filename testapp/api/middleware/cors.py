from collections.abc import Callable
from http import HTTPStatus
from urllib.parse import urlparse

from structlog import get_logger

from ..aws.awsevent import EventV1
from ..exceptions import HttpException

ALLOWED_ORIGINS = [
    "http://localhost:3001",
    "https://d391wccgyuzfh3.cloudfront.net",
    "https://app.test.trilodocs.com",
    "https://*.app.test.trilodocs.com",
]

CORS_HEADERS = {
    "Access-Control-Allow-Methods": "GET,OPTIONS,POST,PUT,PATCH,DELETE",
    "Access-Control-Allow-Headers": "Content-Type,X-Amz-Date,Authorization,X-Api-Key,X-Amz-Security-Token",
    "Access-Control-Allow-Credentials": "true",
}


def get_cors_headers(event: EventV1 | dict) -> dict:
    """Construct CORS headers for API handler response.

    CORS headers from requests containing access credentials must specify allowed origins,
    and cannot use the "*" wildcard.
    More about the CORS policy can be found here: https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS#access-control-allow-origin
    """
    logger = get_logger()
    try:
        headers = (
            event["headers"]
            if (isinstance(event, dict) and "headers" in event)
            else (event.headers if (isinstance(event, EventV1)) else None)
        )
        if not headers:
            raise HttpException(
                status_code=HTTPStatus.BAD_REQUEST, body="No header in request"
            )

        origin = headers.get("origin")
        logger.info("Origin", origin=origin)
        if not origin:
            parsed_referer = urlparse(headers["Referer"])
            logger.info("Parsed ref", parsed_referer=parsed_referer)
            origin = f"{parsed_referer.scheme}://{parsed_referer.netloc}"

        parsed_origin = urlparse(origin)
        for allowed_origin in ALLOWED_ORIGINS:
            parsed_allowed_origin = urlparse(allowed_origin)
            if parsed_origin.scheme == parsed_allowed_origin.scheme:
                if parsed_allowed_origin.netloc == parsed_origin.netloc:
                    return {"Access-Control-Allow-Origin": origin, **CORS_HEADERS}
                elif (
                    parsed_allowed_origin.netloc == "*"
                    or parsed_allowed_origin.netloc.replace("*.", "")
                    in parsed_origin.netloc
                ):
                    return {"Access-Control-Allow-Origin": origin, **CORS_HEADERS}

        return {"Access-Control-Allow-Origin": "", **CORS_HEADERS}

    except KeyError:
        raise HttpException(
            status_code=HTTPStatus.BAD_REQUEST, body="Must supply origin in header"
        )


class CorsMiddleware:
    def __init__(self, next: Callable):
        self.next = next

    def __call__(self, event, context):
        # Do stuff
        _headers = get_cors_headers(event)
        response = self.next(event, context)
        response.headers = (
            {**(response.headers), **_headers} if response.headers else _headers
        )
        return response
