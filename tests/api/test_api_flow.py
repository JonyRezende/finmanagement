import threading

import pytest
import requests

from src.financas.routes import make_server
from tests.fakes import FakeStore


@pytest.fixture
def client():
    store = FakeStore()
    server = make_server(store=store, port=0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = f"http://127.0.0.1:{server.server_address[1]}"
    yield store, url
    server.shutdown()
    server.server_close()


@pytest.fixture
def session(client):
    return requests.Session()


def test_unauthenticated_requests(client, session):
    _, url = client
    assert session.get(url + "/api/me").status_code == 401
    assert session.get(url + "/api/data").status_code == 401


def test_register_login_me_and_logout(client, session):
    _, url = client

    r = session.post(url + "/api/register", json={
        "email": "a@b.com", "password": "senha1234", "password_confirm": "senha1234",
    })
    assert r.status_code == 200
    assert r.json()["email"] == "a@b.com"

    assert session.get(url + "/api/me").json() == {"email": "a@b.com"}
    assert session.get(url + "/api/data").json() == {"recurrences": [], "oneOffs": []}

    assert session.post(url + "/api/logout").status_code == 200
    assert session.get(url + "/api/me").status_code == 401

    r = session.post(url + "/api/login", json={"email": "a@b.com", "password": "senha1234"})
    assert r.status_code == 200
    assert session.get(url + "/api/me").json() == {"email": "a@b.com"}


def test_data_roundtrip(client, session):
    _, url = client
    session.post(url + "/api/register", json={
        "email": "d@b.com", "password": "senha1234", "password_confirm": "senha1234",
    })
    payload = {"recurrences": [{"id": "r1"}], "oneOffs": [{"id": "o1"}]}
    assert session.post(url + "/api/data", json=payload).status_code == 200
    assert session.get(url + "/api/data").json() == payload

    r = session.post(url + "/api/data", json={"recurrences": "nope", "oneOffs": []})
    assert r.status_code == 400


def test_change_password_flow(client, session):
    _, url = client
    session.post(url + "/api/register", json={
        "email": "p@b.com", "password": "senha1234", "password_confirm": "senha1234",
    })

    assert session.post(url + "/api/account/password", json={
        "current_password": "errada", "new_password": "nova12345",
    }).status_code == 401

    assert session.post(url + "/api/account/password", json={
        "current_password": "senha1234", "new_password": "nova12345",
    }).status_code == 200

    assert session.post(url + "/api/login", json={
        "email": "p@b.com", "password": "senha1234",
    }).status_code == 401
    r = session.post(url + "/api/login", json={"email": "p@b.com", "password": "nova12345"})
    assert r.status_code == 200


def test_change_email_flow(client, session):
    store, url = client
    session.post(url + "/api/register", json={
        "email": "e@b.com", "password": "senha1234", "password_confirm": "senha1234",
    })
    session.post(url + "/api/data", json={"recurrences": [{"id": "r1"}], "oneOffs": []})

    r = session.post(url + "/api/account/email", json={
        "current_password": "senha1234", "new_email": "renomeado@b.com",
    })
    assert r.status_code == 200
    assert r.json()["email"] == "renomeado@b.com"

    assert session.get(url + "/api/me").json() == {"email": "renomeado@b.com"}
    assert store.get_user_data("renomeado@b.com")["recurrences"] == [{"id": "r1"}]

    r = session.post(url + "/api/login", json={"email": "e@b.com", "password": "senha1234"})
    assert r.status_code == 401


def test_bad_json_returns_400(client, session):
    _, url = client
    r = session.post(url + "/api/login", data="{invalid", headers={"Content-Type": "application/json"})
    assert r.status_code == 400


def test_security_headers_present(client, session):
    _, url = client
    r = session.get(url + "/")
    assert r.headers["X-Content-Type-Options"] == "nosniff"
    assert r.headers["X-Frame-Options"] == "DENY"
    assert r.headers.get("Content-Security-Policy")
    assert r.headers.get("Strict-Transport-Security")


def test_set_cookie_is_secure_behind_https(client, session):
    _, url = client
    r = session.post(url + "/api/register", headers={"X-Forwarded-Proto": "https"}, json={
        "email": "s@b.com", "password": "senha1234", "password_confirm": "senha1234",
    })
    assert r.status_code == 200
    assert "Secure" in r.headers["Set-Cookie"]
    assert "HttpOnly" in r.headers["Set-Cookie"]


def test_cookie_not_secure_over_plain_http(client, session):
    _, url = client
    r = session.post(url + "/api/register", json={
        "email": "p@b.com", "password": "senha1234", "password_confirm": "senha1234",
    })
    assert r.status_code == 200
    assert "Secure" not in r.headers["Set-Cookie"]


def test_large_body_is_rejected(client, session):
    _, url = client
    big = "x" * (512 * 1024 + 10)
    r = session.post(url + "/api/register", headers={"Content-Type": "application/json"},
                     data=f'{{"email":"big@b.com","password":"{big}","password_confirm":"{big}"}}')
    assert r.status_code == 413