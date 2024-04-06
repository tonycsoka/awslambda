from .endpoints import app

def handler(event, context):
    return app.lambda_handler(event, context)

__all__ = (
    "handler",
)
