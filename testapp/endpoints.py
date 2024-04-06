from http import HTTPStatus
from testapp.api.datatypes import Request, Response
from .api import Api
from datetime import datetime, UTC

app = Api()


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
