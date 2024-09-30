from datetime import UTC, datetime
from http import HTTPStatus

from testapp.api.datatypes import Event, File, Response
from testapp.api.middleware.auth import AuthMiddleware
from testapp.api.middleware.cors import CorsMiddleware

from .api import Api

app = Api()


@app.get("/test/{uid}")
def get_test(uid: str):
    return {"hello": uid}


@app.post("/test/{uid}")
def post_test(uid: str, file: File, resp: Response):
    resp.isBase64Encoded = True
    resp.headers = {"content-type": "image/jpeg"}
    return file.filename


@app.get("/test/{uid}/req/{reqid}")
def get_bob(uid: str, reqid: str, name: str, response: Response, request: Event):
    response.statusCode = HTTPStatus.CREATED
    return {"hello": uid, "world": reqid, "name": name, "date": datetime.now(UTC)}
