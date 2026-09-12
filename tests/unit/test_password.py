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