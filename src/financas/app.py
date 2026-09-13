"""Composição da aplicação: um App reúne os domínios sobre um Store.

Em produção usa o FirestoreStore (credenciais GCP presentes). Localmente, sem
GCP, cai no JsonStore (arquivo JSON no disco). O backend pode ser forçado via
FINANCAS_STORAGE=firestore|local.
"""
import os

from . import config
from .domains import accounts, auth, finance


def _firestore_store():
    from .infra.firestore import FirestoreStore

    return FirestoreStore()


def _json_store():
    from .infra.json_store import JsonStore

    return JsonStore()


def make_default_store():
    backend = os.environ.get("FINANCAS_STORAGE", config.STORAGE_BACKEND)
    if backend == "firestore":
        return _firestore_store()
    if backend == "local":
        return _json_store()
    if os.environ.get("FINANCAS_SA_SECRET") or os.environ.get("GOOGLE_APPLICATION_CREDENTIALS"):
        return _firestore_store()
    return _json_store()


class App:
    def __init__(self, store=None, key_provider=None):
        self.store = store or make_default_store()
        self.auth = auth.AuthService(self.store)
        self.accounts = accounts.AccountsService(self.store, self.auth.sessions)
        self.finance = finance.FinanceService(self.store, key_provider)