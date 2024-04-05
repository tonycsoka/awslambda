from testapp.api.apihandler import Response
from .api import Api
import pytest

app = Api()

@app.get("/test/{uid}")
def get_test(uid:str):
    return {"hello": uid}

@app.post("/test/{uid}")
def post_test(uid:str):
    return {"posted": uid}


@app.get("/test/{uid}/req/{reqid}")
def get_bob(uid:str, reqid:str, name:str, response:Response):
    return {"hello": uid, "world":reqid}

