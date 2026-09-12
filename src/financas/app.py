"""Composição da aplicação: um App reúne os domínios sobre um Store.

Em produção usa o FirestoreStore; os testes injetam um FakeStore.
"""
from .domains import accounts, auth, finance
from .infra.firestore import default_store


class App:
    def __init__(self, store=None):
        self.store = store or default_store
        self.auth = auth.AuthService(self.store)
        self.accounts = accounts.AccountsService(self.store, self.auth.sessions)
        self.finance = finance.FinanceService(self.store)