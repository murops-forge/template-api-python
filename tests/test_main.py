import logging
import re
from types import SimpleNamespace

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


def test_healthz_corpo():
    response = client.get("/healthz")
    assert response.json() == {"status": "ok"}


@pytest.mark.parametrize(
    "name",
    ["a" * 64, "a", "", "José", "日本語", "🚀", "a b&c=d", "<script>"],
)
def test_hello_aceita_nomes_validos(name):
    response = client.get("/hello", params={"name": name})
    assert response.status_code == 200
    assert response.json() == {"message": f"hello, {name}"}


def test_hello_limite_conta_caracteres_e_nao_bytes():
    # 64 caracteres multibyte: dentro do limite
    assert client.get("/hello", params={"name": "é" * 64}).status_code == 200
    assert client.get("/hello", params={"name": "é" * 65}).status_code == 422


def test_hello_nome_longo_detalhe_do_erro():
    response = client.get("/hello", params={"name": "a" * 65})
    detail = response.json()["detail"]
    assert len(detail) == 1
    assert detail[0]["loc"] == ["query", "name"]
    assert detail[0]["type"] == "string_too_long"


def test_hello_ignora_parametro_desconhecido():
    response = client.get("/hello", params={"outro": "x"})
    assert response.status_code == 200
    assert response.json() == {"message": "hello, world"}


def test_hello_usa_primeiro_valor_quando_name_repetido():
    response = client.get("/hello?name=a&name=b")
    assert response.status_code == 200
    assert response.json() == {"message": "hello, b"}


@pytest.mark.parametrize("path", ["/", "/nao-existe", "/hello/extra"])
def test_rota_inexistente_retorna_404(path):
    response = client.get(path, follow_redirects=False)
    assert response.status_code == 404


def test_barra_final_redireciona():
    response = client.get("/healthz/", follow_redirects=False)
    assert response.status_code == 307
    assert response.headers["location"].endswith("/healthz")


@pytest.mark.parametrize("path", ["/healthz", "/hello"])
@pytest.mark.parametrize("method", ["post", "put", "delete", "patch"])
def test_metodo_nao_permitido_retorna_405(path, method):
    response = getattr(client, method)(path)
    assert response.status_code == 405
    assert "GET" in response.headers["allow"]


def test_middleware_loga_requisicao(caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        client.get("/hello", params={"name": "forge"})
    registros = [r.getMessage() for r in caplog.records if r.name == "app"]
    assert len(registros) == 1
    assert re.fullmatch(r"GET /hello 200 \d+\.\dms", registros[0])


def test_middleware_nao_loga_query_string(caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        client.get("/hello", params={"name": "segredo"})
    assert "segredo" not in caplog.text


def test_middleware_loga_status_422(caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        client.get("/hello", params={"name": "a" * 65})
    assert [r.getMessage()[:15] for r in caplog.records if r.name == "app"] == ["GET /hello 422 "]


def test_middleware_loga_404_e_405(caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        client.get("/nao-existe")
        client.post("/hello")
    mensagens = [r.getMessage() for r in caplog.records if r.name == "app"]
    assert mensagens[0].startswith("GET /nao-existe 404 ")
    assert mensagens[1].startswith("POST /hello 405 ")


def test_middleware_nao_loga_healthz(caplog):
    with caplog.at_level(logging.INFO, logger="app"):
        client.get("/healthz")
    assert [r for r in caplog.records if r.name == "app"] == []


def test_middleware_mede_tempo_com_perf_counter(monkeypatch, caplog):
    valores = iter([10.0, 10.25])
    monkeypatch.setattr("app.main.time", SimpleNamespace(perf_counter=lambda: next(valores)))
    with caplog.at_level(logging.INFO, logger="app"):
        client.get("/hello")
    assert "GET /hello 200 250.0ms" in caplog.text
