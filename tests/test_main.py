import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_healthz():
    response = client.get("/healthz")
    assert response.status_code == 200


@pytest.mark.parametrize(
    ("params", "message"),
    [({}, "hello, world"), ({"name": "forge"}, "hello, forge")],
)
def test_hello(params, message):
    response = client.get("/hello", params=params)
    assert response.status_code == 200
    assert response.json() == {"message": message}


def test_hello_rejects_long_name():
    response = client.get("/hello", params={"name": "a" * 65})
    assert response.status_code == 422
