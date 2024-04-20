from .endpoints import app
from structlog import get_logger
import json
import base64


def handler(event, context):
    logger = get_logger()
    response = app.lambda_handler(event, context)
    logger.info("Response from api", response=response)

    body = response.body

    resp = response.model_dump(mode="json")
    if response.isBase64Encoded:
        resp["body"] = body
    return resp


__all__ = ("handler",)
