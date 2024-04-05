import pytest
from testapp.endpoints import app

def get_endpoints() -> list[tuple]:
    ret = []
    for p, dd in app.path_to_params.items():
        for m, pd in dd.items():
            pr = {i:f"Testing{i}" for i in pd.query_params}
            bp = [pd.param_types[i] for i in pd.body_params]
            print(p, m,  pr, bp)
            ret.append((p, m, pr, bp,))
    return ret

@pytest.mark.parametrize("path,method,qp,bp", get_endpoints())
def test_all(path,method,qp,bp):
    print(path, method, qp, bp)
    assert path == 'bob'
    assert True

print(get_endpoints())
