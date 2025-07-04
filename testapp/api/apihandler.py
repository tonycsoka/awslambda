import inspect
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from http import HTTPMethod, HTTPStatus
from typing import Annotated, Any, OrderedDict, get_args, get_origin

from pydantic import BaseModel, ValidationError
from structlog import get_logger

from .aws.awsevent import EventV1
from .datatypes import Body, Context, Event, File, Headers, Response
from .exceptions import HttpException
from .middleware.excep import ExceptionMiddleware


def _populate_parameters(
    f_sig: inspect.Signature, payload: dict, *args, **kwargs
) -> inspect.BoundArguments:
    """
    Populates funcion bound parameters based on the signature, and parameters passed in
    via the payload, args, and kwargs

    Returns the bound args and kwargs

    Takes special care of Api datatypes defined in .datatypes and dependencies using Depends
    """
    skip_bound = False
    for field, param in f_sig.parameters.items():
        an_type = param.annotation
        if an_type == Body:
            kwargs[field] = an_type(payload["body"])
        elif an_type == Context:
            kwargs[field] = an_type(payload["context"])
        elif an_type == Event:
            kwargs[field] = an_type(payload["event"])
        elif an_type == Headers:
            kwargs[field] = an_type(payload["headers"])
        elif an_type == Response:
            kwargs[field] = payload["response"]
        elif inspect.isclass(an_type) and issubclass(an_type, BaseModel):
            kwargs[field] = an_type.model_validate_json(payload["body"])
        elif get_origin(an_type) == Annotated:
            anno_args = get_args(an_type)
            if type(anno_args[1]) is Depends:
                kwargs[field] = anno_args[1](payload=payload)
                skip_bound = True

    bound = f_sig.bind(*args, **kwargs)
    bound.apply_defaults()
    if not skip_bound:
        for k, arg in bound.arguments.items():
            if type(arg) is Depends:
                bound.arguments[k] = arg(payload=payload)
    return bound


class Api:
    @dataclass
    class ParseData:
        func: Callable
        url_params: tuple
        query_params: tuple
        body_params: tuple
        depends: tuple
        param_types: dict
        f_sig: inspect.Signature
        response_status: HTTPStatus

    endpoints: dict[HTTPMethod, OrderedDict[str, ParseData]]
    path_to_params: OrderedDict[str, OrderedDict[HTTPMethod, ParseData]]
    regexes: dict = {
        int: r"(\d+)",
        float: r"(\d+\.+\d*)",
        str: r"([^/\s]+)",
    }
    middleware: list[Callable]

    def __init__(self) -> None:
        self.endpoints = {
            HTTPMethod.DELETE: OrderedDict([]),
            HTTPMethod.GET: OrderedDict([]),
            HTTPMethod.PATCH: OrderedDict([]),
            HTTPMethod.PUT: OrderedDict([]),
            HTTPMethod.POST: OrderedDict([]),
        }
        self.path_to_params = OrderedDict([])
        self.middleware = []

    @staticmethod
    def _process_path(path: str, func: Callable) -> tuple:
        """
        Processes the annotated path and function of and endpoint to
        return the the url types associated with each parameter (path,
        query or a dependency), together with a regex url matcher for
        the path and the python types of each parameter.

        Handles api dataclass and Dependeny
        """
        rpath = f"{path.rstrip('/')}"

        query_params = []
        body_params = []
        depends = []
        param_types = {}

        f_sig = inspect.signature(func)

        url_params = tuple(re.findall(r"(?:\{([\w-]*)\})", path))
        for field, param in f_sig.parameters.items():
            annotation = param.annotation
            if field in url_params:
                rpath = rpath.replace(r"{{{}}}".format(field), Api.regexes[annotation])
                param_types[field] = annotation
            elif annotation and annotation in [Body, File, Event, Context, Headers]:
                if annotation in [Body, File]:
                    body_params.append(field)
                    param_types[field] = annotation
                if annotation == Headers:
                    depends.append(field)
                    param_types[field] = annotation
            elif inspect.isclass(annotation) and issubclass(annotation, Response):
                depends.append(field)
                param_types[field] = annotation
            elif inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                body_params.append(field)
                param_types[field] = annotation
            elif annotation and get_origin(annotation) == Annotated:
                anno_args = get_args(annotation)
                if type(anno_args[1]) is Depends:
                    depends.append(field)
                    param_types[field] = annotation
            else:
                query_params.append(field)
                param_types[field] = annotation
        rpath = f"{rpath}$"

        return (
            rpath,
            f_sig,
            url_params,
            tuple(query_params),
            tuple(body_params),
            tuple(depends),
            param_types,
        )

    def _add_api_endpoint(
        self, method: str, path: str, func: Callable, status_code: HTTPStatus
    ) -> Callable:
        logger = get_logger()
        rpath, f_sig, url_params, query_params, body_params, depends, param_types = (
            Api._process_path(path, func)
        )

        @wraps(func)
        def call_api_endpoint(payload: dict, *args, **kwargs) -> Callable:
            try:
                bound = _populate_parameters(f_sig, payload, *args, **kwargs)
                return func(*bound.args, **bound.kwargs)
            except TypeError as err:
                raise HttpException(
                    status_code=HTTPStatus.NOT_FOUND, body=err.__str__()
                )
            except ValidationError as err:
                raise HttpException(
                    status_code=HTTPStatus.BAD_REQUEST, body=err.__str__()
                )

        parsed_data = Api.ParseData(
            func=call_api_endpoint,
            url_params=url_params,
            query_params=query_params,
            body_params=body_params,
            depends=depends,
            param_types=param_types,
            f_sig=f_sig,
            response_status=status_code,
        )
        self.endpoints[HTTPMethod(method)][rpath] = parsed_data
        if path not in self.path_to_params:
            self.path_to_params[path] = OrderedDict()
        if HTTPMethod(method) not in self.path_to_params[path]:
            self.path_to_params[path][HTTPMethod(method)] = parsed_data
        logger.info("Registered path", path=path, rpath=rpath)
        return call_api_endpoint

    def get(self, path: str, status_code: HTTPStatus = HTTPStatus.OK) -> Callable:
        def deco(func: Callable) -> Callable:
            return self._add_api_endpoint(HTTPMethod.GET, path, func, status_code)

        return deco

    def put(self, path: str, status_code: HTTPStatus = HTTPStatus.OK) -> Callable:
        def deco(func: Callable) -> Callable:
            return self._add_api_endpoint(HTTPMethod.PUT, path, func, status_code)

        return deco

    def post(self, path: str, status_code: HTTPStatus = HTTPStatus.OK) -> Callable:
        def deco(func: Callable) -> Callable:
            return self._add_api_endpoint(HTTPMethod.POST, path, func, status_code)

        return deco

    def patch(self, path: str, status_code: HTTPStatus = HTTPStatus.OK) -> Callable:
        def deco(func: Callable) -> Callable:
            return self._add_api_endpoint(HTTPMethod.PATCH, path, func, status_code)

        return deco

    def delete(self, path: str, status_code: HTTPStatus = HTTPStatus.OK) -> Callable:
        def deco(func: Callable) -> Callable:
            return self._add_api_endpoint(HTTPMethod.DELETE, path, func, status_code)

        return deco

    def lambda_handler(self, event, context):
        logger = get_logger()
        event = Api.make_event(event)
        logger.debug(event)

        func = self._lambda_handler

        for f in self.middleware:
            func = f(func)
        logger.info("Adding ExceptionMiddleware")
        func = ExceptionMiddleware(func)

        return func(event, context)

    @staticmethod
    def make_event(event) -> EventV1:
        return Event(event=event).event

    @staticmethod
    def parse_event(event: EventV1) -> tuple:
        try:
            params = event.queryStringParameters
            raw_path = event.path
            method = event.httpMethod
            content = event.body
            headers = event.headers
            return params, raw_path, method, content, headers
        except Exception as e:
            raise HttpException(status_code=HTTPStatus.BAD_REQUEST, body=e) from e

    def _lambda_handler(self, event, context) -> Response:
        logger = get_logger()
        params, raw_path, method, content, headers = Api.parse_event(event)

        logger.info(
            "Handling request",
            Raw_path=raw_path,
            Method=method,
            Event=event,
            Context=context,
        )

        return self.handler(
            method=method,
            full_path=raw_path,
            query_params=params,
            event=event,
            context=context,
            body=content,
            headers=headers,
        )

    def add_middleware(self, middleware: Callable):
        logger = get_logger()
        logger.info("Adding middleware", middleware=middleware)
        self.middleware.append(middleware)

    def handler(
        self,
        method: str,
        full_path: str,
        *,
        query_params: dict,
        event: EventV1,
        context: Any,
        body: Any,
        headers: dict,
    ) -> Response:
        logger = get_logger()
        if not query_params:
            query_params = {}
        for rpath, parse_d in self.endpoints[HTTPMethod(method)].items():
            if values := re.match(rpath, full_path.rstrip("/")):
                logger.info(
                    "Handler",
                    method=method,
                    full_path=full_path,
                    query_params=query_params,
                    body=body,
                )
                logger.info("Found path", ep_path=rpath)
                response = Response(statusCode=parse_d.response_status)
                params = {}
                for i, j in zip(parse_d.url_params, values.groups()):
                    if param := parse_d.f_sig.parameters.get(i):
                        params[i] = param.annotation(j)
                    else:
                        logger.info("unknown param", param=i)

                for i, j in query_params.items():
                    if param := parse_d.f_sig.parameters.get(i):
                        params[i] = param.annotation(j)
                    else:
                        logger.info("unknown param", param=i)

                payload = {
                    "event": event,
                    "context": context,
                    "body": body,
                    "headers": headers,
                    "response": response,
                }

                body = parse_d.func(payload, **params)
                if body:
                    response.body = body
                return response
        logger.info("No path found", requested_path=full_path)
        return Response(statusCode=HTTPStatus.NOT_FOUND, body="Unknown path")


class Depends:
    cache: dict[Callable, Any] = {}
    dependency_overrides: dict[Callable, Callable] = {}

    def __init__(self, dependency: Callable[..., Any], use_cache=False):
        self.dependency = dependency
        self.use_cache = use_cache

    def __call__(self, payload, *args, **kwargs) -> Any:
        if self.dependency in Depends.dependency_overrides:
            dep = Depends.dependency_overrides[self.dependency]
            return dep()

        if self.use_cache and self.dependency in Depends.cache:
            return Depends.cache[self.dependency]

        f_sig = inspect.signature(self.dependency)
        bound = _populate_parameters(f_sig, payload, *args, **kwargs)

        result = self.dependency(*bound.args, **bound.kwargs)
        if self.use_cache:
            Depends.cache[self.dependency] = result
        return result
