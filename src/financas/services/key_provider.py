"""Provedor da chave-mestra da criptografia dos dados financeiros.

Produção: chave base64 de 32 bytes lida do Secret Manager
(FINANCAS_ENCRYPTION_SECRET). Desenvolvimento: variável de ambiente
FINANCAS_ENCRYPTION_KEY. A chave é carregada uma única vez e mantida em memória.
"""
import base64
import os

from .. import config
from ..errors import Error

KEY_BYTES = 32


class DataKeyProvider:
    def __init__(self, secret_client=None):
        self._secret_client = secret_client
        self._master_key = None

    def get_master_key(self):
        if self._master_key is None:
            self._master_key = self._load_master_key()
        return self._master_key

    def _load_master_key(self):
        secret_name = os.environ.get(config.ENCRYPTION_SECRET_ENV, "")
        if secret_name:
            raw = self._fetch_from_secret_manager(secret_name)
        else:
            raw = os.environ.get(config.ENCRYPTION_KEY_ENV, "")
        if not raw:
            raise Error(
                "Chave de criptografia não configurada "
                f"({config.ENCRYPTION_KEY_ENV} ou {config.ENCRYPTION_SECRET_ENV})",
                status=500,
            )
        return _decode_key(raw.strip())

    def _fetch_from_secret_manager(self, secret_name):
        client = self._secret_client
        if client is None:
            from google.cloud import secretmanager

            client = secretmanager.SecretManagerServiceClient()
        response = client.access_secret_version(name=secret_name)
        return response.payload.data.decode("utf-8")


def _decode_key(raw):
    try:
        key = base64.b64decode(raw)
    except ValueError:
        raise Error("Chave de criptografia inválida (é preciso ser base64)", status=500) from None
    if len(key) != KEY_BYTES:
        raise Error(f"A chave de criptografia deve ter exatamente {KEY_BYTES} bytes", status=500)
    return key