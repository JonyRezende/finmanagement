"""Domínio de dados financeiros: leitura/escrita com criptografia em repouso.

Os dados sensíveis (recorrências, lançamentos) são cifrados com AES-GCM antes de
serem gravados no store. O formato legado em texto puro ainda é lido (fallback
de migração); o contrato da API permanece em JSON legível para o frontend.
"""
from ..errors import Error
from ..services import crypto
from ..services.key_provider import DataKeyProvider


class FinanceService:
    def __init__(self, store, key_provider=None):
        self._store = store
        self._key_provider = key_provider or DataKeyProvider()

    def get_data(self, email):
        data = self._store.get_user_data(email)
        if not data:
            return {"recurrences": [], "oneOffs": []}
        if crypto.is_encrypted(data):
            user_key = self._user_key(email)
            return crypto.decrypt_json(user_key, data)
        return {
            "recurrences": data.get("recurrences", []),
            "oneOffs": data.get("oneOffs", []),
        }

    def save_data(self, email, payload):
        recurrences = payload.get("recurrences", [])
        one_offs = payload.get("oneOffs", [])
        if not isinstance(recurrences, list) or not isinstance(one_offs, list):
            raise Error("Formato inválido")
        user_key = self._user_key(email)
        self._store.save_user_data(email, crypto.encrypt_json(user_key, {
            "recurrences": recurrences,
            "oneOffs": one_offs,
        }))

    def _user_key(self, email):
        return crypto.derive_user_key(self._key_provider.get_master_key(), email)