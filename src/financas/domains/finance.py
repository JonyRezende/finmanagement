"""Domínio de dados financeiros: leitura/escrita com validação básica."""
from ..errors import Error


class FinanceService:
    def __init__(self, store):
        self._store = store

    def get_data(self, email):
        data = self._store.get_user_data(email) or {"recurrences": [], "oneOffs": []}
        return {
            "recurrences": data.get("recurrences", []),
            "oneOffs": data.get("oneOffs", []),
        }

    def save_data(self, email, payload):
        recurrences = payload.get("recurrences", [])
        one_offs = payload.get("oneOffs", [])
        if not isinstance(recurrences, list) or not isinstance(one_offs, list):
            raise Error("Formato inválido")
        self._store.save_user_data(email, {
            "recurrences": recurrences,
            "oneOffs": one_offs,
        })