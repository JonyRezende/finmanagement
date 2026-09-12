import hashlib
import os

import pytest

from src.financas.domains import auth as auth_domain
from src.financas.errors import Error
from src.financas.services import password as pwd
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


def _save_legacy_user(svc, email="a@b.com"):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", "senha1234".encode("utf-8"), salt, pwd.LEGACY_PBKDF2_ITERATIONS
    )
    svc._store.save_user_auth(email, {
        "email": email,
        "salt": salt.hex(),
        "password_hash": digest.hex(),
        "created_at": 0,
    })
    svc._store.save_user_data(email, {"recurrences": [], "oneOffs": []})


def test_login_upgrades_legacy_hash():
    svc = make_auth()
    _save_legacy_user(svc)

    token = svc.login("a@b.com", "senha1234")
    assert svc.email_for(token) == "a@b.com"

    user = svc._store.get_user_auth("a@b.com")
    assert pwd.verify_password("senha1234", user["salt"], user["password_hash"])
    assert not pwd.verify_legacy_password("senha1234", user["salt"], user["password_hash"])


def test_login_rejects_wrong_password_on_legacy_hash():
    svc = make_auth()
    _save_legacy_user(svc)

    with pytest.raises(Error):
        svc.login("a@b.com", "errada")
    user = svc._store.get_user_auth("a@b.com")
    assert pwd.verify_legacy_password("senha1234", user["salt"], user["password_hash"])