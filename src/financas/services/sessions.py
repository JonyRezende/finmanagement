"""Sessões persistentes com TTL e cache em memória.

O store (com save_session/get_session/delete_session/list_sessions) é
injetável para permitir testes offline; em produção o App passa o
FirestoreStore.
"""
import secrets
import time
from collections import OrderedDict

SESSION_TTL_DAYS = 30
MAX_CACHED_SESSIONS = 500


class SessionService:
    def __init__(self, store):
        self._store = store
        self._cache = OrderedDict()

    def _touch(self, token):
        if token in self._cache:
            self._cache.move_to_end(token)

    def _evict(self):
        while len(self._cache) > MAX_CACHED_SESSIONS:
            self._cache.popitem(last=False)

    def create(self, email):
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + SESSION_TTL_DAYS * 86400
        self._store.save_session(token, email, expires_at)
        self._cache[token] = email
        self._evict()
        return token

    def email_for(self, token):
        if token in self._cache:
            self._touch(token)
            return self._cache[token]
        data = self._store.get_session(token)
        if not data:
            return None
        expires_at = data.get("expires_at") or 0
        if time.time() >= expires_at:
            self._store.delete_session(token)
            return None
        email = data.get("email")
        if email:
            self._cache[token] = email
            self._evict()
        return email

    def destroy(self, token):
        self._cache.pop(token, None)
        self._store.delete_session(token)

    def destroy_for_email(self, email, except_token=None):
        for token in self._store.list_sessions(email):
            if token != except_token:
                self.destroy(token)

    def update_email(self, token, new_email):
        if token in self._cache:
            self._cache[token] = new_email
        data = self._store.get_session(token)
        if data:
            self._store.save_session(token, new_email, data.get("expires_at") or time.time())