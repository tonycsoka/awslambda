from http import HTTPStatus
from testapp.api.datatypes import Request, Response
from testapp.api.middleware.auth import AuthMiddleware
from testapp.api.middleware.cors import CorsMiddleware
from .api import Api
from datetime import datetime, UTC

app = Api()
app.add_middleware(CorsMiddleware)
app.add_middleware(AuthMiddleware)


@app.get("/test/{uid}")
def get_test(uid: str):
    return {"hello": uid}


@app.post("/test/{uid}")
def post_test(uid: str):
    return {"posted": uid}


@app.get("/test/{uid}/req/{reqid}")
def get_bob(uid: str, reqid: str, name: str, response: Response, request: Request):
    response.statusCode = HTTPStatus.CREATED
    return {"hello": uid, "world": reqid, "name": name, "date": datetime.now(UTC)}
