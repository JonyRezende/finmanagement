import pytest

from src.financas.domains import auth as auth_domain
from src.financas.errors import Error
from tests.fakes import FakeStore


def make_auth():
    return auth_domain.AuthService(FakeStore())


def test_register_creates_session():
    svc = make_auth()
    token = svc.register("A@b.com", "senha1234", "senha1234")
    assert svc.email_for(token) == "a@b.com"


def test_register_invalid_email():
    svc = make_auth()
    with pytest.raises(Error):
        svc.register("invalido", "senha1234", "senha1234")


def test_register_short_password():
    svc = make_auth()
    with pytest.raises(Error):
        svc.register("a@b.com", "123", "123")


def test_register_password_mismatch():
    svc = make_auth()
    with pytest.raises(Error):
        svc.register("a@b.com", "senha1234", "outra1234")


def test_register_duplicate_email():
    svc = make_auth()
    svc.register("a@b.com", "senha1234", "senha1234")
    with pytest.raises(Error):
        svc.register("a@b.com", "senha1234", "senha1234")


def test_login_success_and_failure():
    svc = make_auth()
    svc.register("a@b.com", "senha1234", "senha1234")
    token = svc.login("a@b.com", "senha1234")
    assert svc.email_for(token) == "a@b.com"
    with pytest.raises(Error):
        svc.login("a@b.com", "errada")


def test_logout_destroys_session():
    svc = make_auth()
    token = svc.register("a@b.com", "senha1234", "senha1234")
    svc.logout(token)
    assert svc.email_for(token) is None


def test_login_blocks_after_many_failures():
    from src.financas.services import rate_limit
    rate_limit.reset()
    svc = make_auth()
    for _ in range(rate_limit.MAX_ATTEMPTS):
        with pytest.raises(Error):
            svc.login("a@b.com", "errada")
    with pytest.raises(Error) as exc:
        svc.login("a@b.com", "errada")
    assert exc.value.status == 429
    rate_limit.reset()