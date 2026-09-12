import pytest

from src.financas.domains import accounts as accounts_domain
from src.financas.domains import auth as auth_domain
from src.financas.errors import Error
from tests.fakes import FakeStore


def make_svc():
    store = FakeStore()
    auth = auth_domain.AuthService(store)
    accounts = accounts_domain.AccountsService(store, auth.sessions)
    return store, auth, accounts


def test_change_password_ok():
    _, auth, accounts = make_svc()
    token = auth.register("a@b.com", "senha1234", "senha1234")
    accounts.change_password("a@b.com", "senha1234", "nova12345")
    auth.logout(token)
    new_token = auth.login("a@b.com", "nova12345")
    assert new_token


def test_change_password_wrong_current():
    _, auth, accounts = make_svc()
    auth.register("a@b.com", "senha1234", "senha1234")
    with pytest.raises(Error) as exc:
        accounts.change_password("a@b.com", "errada", "nova12345")
    assert exc.value.status == 401


def test_change_password_too_short():
    _, auth, accounts = make_svc()
    auth.register("a@b.com", "senha1234", "senha1234")
    with pytest.raises(Error):
        accounts.change_password("a@b.com", "senha1234", "123")


def test_change_email_ok_moves_data_and_session():
    store, auth, accounts = make_svc()
    token = auth.register("a@b.com", "senha1234", "senha1234")
    store.save_user_data("a@b.com", {"recurrences": [{"id": "r1"}], "oneOffs": []})
    new_email = accounts.change_email("a@b.com", token, "senha1234", "novo@b.com")
    assert new_email == "novo@b.com"
    assert auth.email_for(token) == "novo@b.com"
    assert store.get_user_data("novo@b.com")["recurrences"][0]["id"] == "r1"
    assert store.get_user_auth("a@b.com") is None


def test_change_email_wrong_password():
    _, auth, accounts = make_svc()
    token = auth.register("a@b.com", "senha1234", "senha1234")
    with pytest.raises(Error) as exc:
        accounts.change_email("a@b.com", token, "errada", "novo@b.com")
    assert exc.value.status == 401


def test_change_email_conflict():
    _, auth, accounts = make_svc()
    token = auth.register("a@b.com", "senha1234", "senha1234")
    auth.register("x@b.com", "senha1234", "senha1234")
    with pytest.raises(Error) as exc:
        accounts.change_email("a@b.com", token, "senha1234", "x@b.com")
    assert exc.value.status == 409


def test_change_password_other_sessions_survive():
    _, auth, accounts = make_svc()
    token = auth.register("a@b.com", "senha1234", "senha1234")
    accounts.change_password("a@b.com", "senha1234", "nova12345")
    assert auth.email_for(token) == "a@b.com"