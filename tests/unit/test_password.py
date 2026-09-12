import hashlib
import os

from src.financas.services import password


def test_hash_verify_roundtrip():
    salt, digest = password.hash_password("senha1234")
    assert password.verify_password("senha1234", salt, digest)


def test_wrong_password_fails():
    salt, digest = password.hash_password("senha1234")
    assert not password.verify_password("errada", salt, digest)


def test_salt_is_unique():
    salt1, _ = password.hash_password("senha1234")
    salt2, _ = password.hash_password("senha1234")
    assert salt1 != salt2


def test_same_password_different_hashes():
    _, h1 = password.hash_password("senha1234")
    _, h2 = password.hash_password("senha1234")
    assert h1 != h2


def _legacy_hash(value):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", value.encode("utf-8"), salt, password.LEGACY_PBKDF2_ITERATIONS
    )
    return salt.hex(), digest.hex()


def test_legacy_hash_fails_at_current_iterations():
    salt, digest = _legacy_hash("senha1234")
    assert not password.verify_password("senha1234", salt, digest)
    assert password.verify_legacy_password("senha1234", salt, digest)


def test_verify_password_current_accepts_current_and_legacy():
    salt, digest = password.hash_password("senha1234")
    assert password.verify_password_current("senha1234", salt, digest)

    legacy_salt, legacy_digest = _legacy_hash("senha1234")
    assert password.verify_password_current("senha1234", legacy_salt, legacy_digest)
    assert not password.verify_password_current("errada", legacy_salt, legacy_digest)