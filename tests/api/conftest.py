import base64
import os

import pytest


@pytest.fixture(autouse=True)
def _encryption_key_env(monkeypatch):
    monkeypatch.setenv("FINANCAS_ENCRYPTION_KEY", base64.b64encode(os.urandom(32)).decode("ascii"))
    monkeypatch.delenv("FINANCAS_ENCRYPTION_SECRET", raising=False)