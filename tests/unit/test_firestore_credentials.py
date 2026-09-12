import json
import types

from src.financas.infra import firestore as fs


def _private_key_pem():
    from cryptography.hazmat.primitives import serialization
    from cryptography.hazmat.primitives.asymmetric import rsa

    key = rsa.generate_private_key(public_exponent=65537, key_size=1024)
    return key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    ).decode()


def test_no_credential_without_secret_env(monkeypatch):
    monkeypatch.delenv("FINANCAS_SA_SECRET", raising=False)
    assert fs._sa_credentials() is None


class FakeSecretClient:
    def __init__(self, data):
        self._data = data

    def access_secret_version(self, name):
        return types.SimpleNamespace(payload=types.SimpleNamespace(data=self._data))


def test_loads_credentials_from_secret(monkeypatch):
    monkeypatch.setenv("FINANCAS_SA_SECRET", "projects/p/secrets/s/versions/latest")
    payload = json.dumps({
        "type": "service_account",
        "project_id": "p",
        "private_key_id": "k",
        "private_key": _private_key_pem(),
        "client_email": "app@example.iam.gserviceaccount.com",
        "client_id": "1",
        "token_uri": "https://oauth2.googleapis.com/token",
    }).encode("utf-8")
    creds = fs._sa_credentials(secret_client=FakeSecretClient(payload))
    assert creds.service_account_email == "app@example.iam.gserviceaccount.com"