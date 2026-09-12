import time

from src.financas.services.sessions import SessionService


class FakeStore:
    def __init__(self):
        self.docs = {}

    def save(self, token, email, expires_at):
        self.docs[token] = {"email": email, "expires_at": expires_at}

    def get(self, token):
        return self.docs.get(token)

    def delete(self, token):
        self.docs.pop(token, None)


def make_service():
    return SessionService(store=FakeStore())


def test_create_and_read():
    svc = make_service()
    token = svc.create("a@b.com")
    assert svc.email_for(token) == "a@b.com"


def test_survives_memory_clear():
    svc = make_service()
    token = svc.create("a@b.com")
    svc._cache.clear()
    assert svc.email_for(token) == "a@b.com"


def test_unknown_token_returns_none():
    svc = make_service()
    assert svc.email_for("nope") is None


def test_expired_session_is_deleted():
    svc = make_service()
    token = svc.create("a@b.com")
    store = svc._store
    store.docs[token]["expires_at"] = time.time() - 1
    svc._cache.clear()
    assert svc.email_for(token) is None
    assert token not in store.docs


def test_destroy_removes():
    svc = make_service()
    token = svc.create("a@b.com")
    svc.destroy(token)
    assert svc.email_for(token) is None


def test_update_email_keeps_session_alive():
    svc = make_service()
    token = svc.create("a@b.com")
    svc.update_email(token, "novo@b.com")
    assert svc.email_for(token) == "novo@b.com"