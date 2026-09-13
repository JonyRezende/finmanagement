import base64
import types

import pytest

from src.financas import config
from src.financas.errors import Error
from src.financas.services import key_provider


def _test_key_b64():
    return base64.b64encode(bytes(32)).decode("ascii")


class FakeSecretClient:
    def __init__(self, data):
        self._data = data

    def access_secret_version(self, name):
        return types.SimpleNamespace(payload=types.SimpleNamespace(data=self._data))


def test_loads_key_from_env(monkeypatch):
    key = _test_key_b64()
    monkeypatch.setenv(config.ENCRYPTION_KEY_ENV, key)
    monkeypatch.delenv(config.ENCRYPTION_SECRET_ENV, raising=False)
    assert key_provider.DataKeyProvider().get_master_key() == bytes(32)


def test_caches_key_in_memory(monkeypatch):
    key = _test_key_b64()
    monkeypatch.setenv(config.ENCRYPTION_KEY_ENV, key)
    monkeypatch.delenv(config.ENCRYPTION_SECRET_ENV, raising=False)
    provider = key_provider.DataKeyProvider()
    assert provider.get_master_key() == bytes(32)
    assert provider.get_master_key() == bytes(32)


def test_loads_key_from_secret_manager(monkeypatch):
    key = _test_key_b64()
    secret_name = "projects/p/secrets/s/versions/latest"
    monkeypatch.setenv(config.ENCRYPTION_SECRET_ENV, secret_name)
    provider = key_provider.DataKeyProvider(secret_client=FakeSecretClient(key.encode("utf-8")))
    assert provider.get_master_key() == bytes(32)


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv(config.ENCRYPTION_KEY_ENV, raising=False)
    monkeypatch.delenv(config.ENCRYPTION_SECRET_ENV, raising=False)
    with pytest.raises(Error):
        key_provider.DataKeyProvider().get_master_key()


def test_short_key_rejected(monkeypatch):
    monkeypatch.setenv(config.ENCRYPTION_KEY_ENV, base64.b64encode(b"curta").decode("ascii"))
    monkeypatch.delenv(config.ENCRYPTION_SECRET_ENV, raising=False)
    with pytest.raises(Error):
        key_provider.DataKeyProvider().get_master_key()


def test_invalid_base64_key_rejected(monkeypatch):
    monkeypatch.setenv(config.ENCRYPTION_KEY_ENV, "not-base64!!!")
    monkeypatch.delenv(config.ENCRYPTION_SECRET_ENV, raising=False)
    with pytest.raises(Error):
        key_provider.DataKeyProvider().get_master_key()