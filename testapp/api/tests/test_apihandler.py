from collections.abc import Callable
from http import HTTPMethod, HTTPStatus
from unittest.mock import MagicMock, create_autospec

from trilodocs.api import Api
from trilodocs.api.apihandler import Depends


def test_add_api_endpoint():
    api = Api()

    @api.get("/test")
    def test_ep():
        return "Test"

    assert len(api.endpoints[HTTPMethod.GET]) == 1
    assert len(api.path_to_params) == 1
    assert api.endpoints[HTTPMethod.GET]["/test$"].func.__name__ == "test_ep"
    assert api.endpoints[HTTPMethod.GET]["/test$"].response_status == HTTPStatus.OK


def test_lambda_handler():
    api = Api()

    @api.get("/test")
    def test_ep():
        return "Test"

    event = {"version": "1.0", "httpMethod": "GET", "path": "/test"}
    context = {}

    response = api.lambda_handler(event, context)
    assert response.statusCode == HTTPStatus.OK
    assert response.body == "Test"


def test_depends():
    def func(key):
        return key

    dependency = create_autospec(func)
    dependency.return_value = 42

    depends = Depends(dependency)

    kwargs = {"key": "value"}

    assert depends({}, *[], **kwargs) == 42
    dependency.assert_called_once_with("value")


def test_depends_override():

    def func(key):
        return key

    dependency = create_autospec(func)
    dependency.return_value = 42
    override = MagicMock(return_value=808)

    depends = Depends(dependency)
    Depends.dependency_overrides[dependency] = override

    kwargs = {"key": "value"}

    assert depends({}, *[], **kwargs) == 808
    override.assert_called_once()
    dependency.assert_not_called()


def test_unhandled_excep():

    api = Api()

    class DummyMiddleware:
        def __init__(self, next: Callable):
            self.next = next

        def __call__(self, event, context):
            raise NotImplemented()

    api.add_middleware(DummyMiddleware)

    @api.get("/test")
    def test_ep():
        return "Test"

    event = {"version": "1.0", "httpMethod": "GET", "path": "/test"}
    context = {}

    response = api.lambda_handler(event, context)
    assert response.statusCode == HTTPStatus.INTERNAL_SERVER_ERROR
