import inspect
import re
from collections.abc import Callable
from dataclasses import dataclass
from functools import wraps
from http import HTTPMethod, HTTPStatus
from typing import Annotated, Any, OrderedDict, get_args, get_origin

from pydantic import BaseModel, ValidationError
from structlog import get_logger

from .middleware.excep import ExceptionMiddleware

from .middleware import CORS_HEADERS
from .multipart import MultipartDecoder


def _populate_parameters(f_sig, payload, *args, **kwargs):
    skip_bound = False
    for field, param in f_sig.parameters.items():
        an_type = param.annotation
        if an_type == File:
            kwargs[field] = File(
                content=payload["body"], headers=Headers(payload["headers"])
            )
        elif an_type == Body:
            kwargs[field] = Body(payload["body"])
        elif an_type == Context:
            kwargs[field] = Context(body=payload["context"])
        elif an_type == Event:
            kwargs[field] = Event(body=payload["event"])
        elif an_type == Headers:
            kwargs[field] = Headers(payload["headers"])
        elif inspect.isclass(an_type) and issubclass(an_type, BaseModel):
            kwargs[field] = an_type(**payload["body"])
        elif get_origin(an_type) == Annotated:
            anno_args = get_args(an_type)
            if type(anno_args[1]) == Depends:
                kwargs[field] = anno_args[1](payload=payload)
                skip_bound = True

    bound = f_sig.bind(*args, **kwargs)
    bound.apply_defaults()
    if not skip_bound:
        for k, arg in bound.arguments.items():
            if type(arg) == Depends:
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
    def _process_path(path: str, func: Callable):
        rpath = r"{}".format(path.rstrip("/"))

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
            elif inspect.isclass(annotation) and issubclass(annotation, BaseModel):
                body_params.append(field)
                param_types[field] = annotation
            elif annotation and get_origin(annotation) == Annotated:
                anno_args = get_args(annotation)
                if type(anno_args[1]) == Depends:
                    depends.append(field)
                    param_types[field] = annotation
            else:
                query_params.append(field)
                param_types[field] = annotation
        rpath = rpath + r"$"

        return (
            rpath,
            f_sig,
            url_params,
            tuple(query_params),
            tuple(body_params),
            tuple(depends),
            param_types,
        )

    def _add_api_endpoint(self, method: str, path: str, func: Callable):
        rpath, f_sig, url_params, query_params, body_params, depends, param_types = (
            Api._process_path(path, func)
        )

        @wraps(func)
        def call_api_endpoint(payload: dict, *args, **kwargs):
            try:
                bound = _populate_parameters(f_sig, payload, *args, **kwargs)
                return func(*bound.args, **bound.kwargs)
            except TypeError as err:
                return {"status": HTTPStatus.NOT_FOUND.value, "message": f"{err}"}
            except ValidationError as err:
                return {
                    "status": HTTPStatus.BAD_REQUEST.value,
                    "message": f"{err.json()}",
                }

        parsed_data = Api.ParseData(
            func=call_api_endpoint,
            url_params=url_params,
            query_params=query_params,
            body_params=body_params,
            depends=depends,
            param_types=param_types,
            f_sig=f_sig,
        )
        self.endpoints[HTTPMethod(method)][rpath] = parsed_data
        if not path in self.path_to_params:
            self.path_to_params[path] = OrderedDict()
        self.path_to_params[path][HTTPMethod(method)] = parsed_data
        print(f"Registered path : {rpath}")
        print(f"Signature : {f_sig}")
        return call_api_endpoint

    def get(self, path: str):
        def deco(func: Callable):
            return self._add_api_endpoint(HTTPMethod.GET, path, func)

        return deco

    def put(self, path: str):
        def deco(func: Callable):
            return self._add_api_endpoint(HTTPMethod.PUT, path, func)

        return deco

    def post(self, path: str):
        def deco(func: Callable):
            return self._add_api_endpoint(HTTPMethod.POST, path, func)

        return deco

    def patch(self, path: str):
        def deco(func: Callable):
            return self._add_api_endpoint(HTTPMethod.PATCH, path, func)

        return deco

    def delete(self, path: str):
        def deco(func: Callable):
            return self._add_api_endpoint(HTTPMethod.DELETE, path, func)

        return deco

    def lambda_handler(self, event, context):
        logger = get_logger()
        logger.debug(event)

        func = self._lambda_handler

        for f in self.middleware:
            func = f(func)
        func = ExceptionMiddleware(func)

        response = func(event, context)
        return response

    def _lambda_handler(self, event, context):
        logger = get_logger()
        params = event.get("queryStringParameters")
        raw_path = event.get("path", "")
        method = event.get("httpMethod")
        content = event.get("body")
        headers = event.get("headers")

        logger.info("Handling request", raw_path=raw_path, method=method)

        api_out = self.handler(
            method=method,
            full_path=raw_path,
            query_params=params,
            event=event,
            context=context,
            body=content,
            headers={**headers, **CORS_HEADERS},
        )

        return api_out

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
        event: dict,
        context: dict,
        body: dict,
        headers: dict,
    ):
        if not query_params:
            query_params = {}
        for rpath, parse_d in self.endpoints[HTTPMethod(method)].items():
            values = re.match(rpath, full_path.rstrip("/"))
            if values:
                params = {}
                for i, j in zip(parse_d.url_params, values.groups()):
                    if param := parse_d.f_sig.parameters.get(i):
                        params[i] = param.annotation(j)
                    else:
                        print(f"unknown param: {i}")

                for i, j in query_params.items():
                    if param := parse_d.f_sig.parameters.get(i):
                        params[i] = param.annotation(j)
                    else:
                        print(f"unknown param: {i}")

                payload = {
                    "event": event,
                    "context": context,
                    "body": body,
                    "headers": headers,
                }

                return parse_d.func(payload, **params)
        return {
            "statusCode": HTTPStatus.NOT_FOUND.value,
            "body": "Unknown path",
        }


class Context:
    data: dict

    def __init__(self, body: dict):
        self.data = body


class Event:
    data: dict

    def __init__(self, body: dict):
        self.data = body


class Body(str):
    pass


class Headers(dict):
    pass


class File:
    headers: Headers
    content: str

    def __init__(self, content: str, headers: Headers):
        self.content = content
        self.headers = headers
        self.extract_file()

    def extract_file(self):
        content_type = self.headers["Content-Type"]

        multipart_data = MultipartDecoder(self.content, content_type)

        filename = None
        part = multipart_data.parts[0]
        content = part.content
        disposition = part.headers[b"Content-Disposition"]
        for content_info in str(disposition).split(";"):
            info = content_info.split("=", 2)
            if info[0].strip() == "filename":
                filename = info[1].strip("\"'\t \r\n")
        assert filename is not None
        self.filename = filename
        self.file = content


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