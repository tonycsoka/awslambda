from .endpoints import app
from structlog import get_logger

def handler(event, context):
    logger = get_logger()
    response = app.lambda_handler(event, context)
    logger.info("Response from api", response=response)
    return response

__all__ = (
    "handler",
)
