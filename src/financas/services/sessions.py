"""Sessões persistentes com TTL e cache em memória.

O store é injetável para permitir testes offline; por padrão grava no
Firestore via infra.firestore.
"""
import secrets
import time

from ..infra import firestore

SESSION_TTL_DAYS = 30


class _FirestoreSessionStore:
    def save(self, token, email, expires_at):
        firestore.save_session(token, email, expires_at)

    def get(self, token):
        return firestore.get_session(token)

    def delete(self, token):
        firestore.delete_session(token)


class SessionService:
    def __init__(self, store=None):
        self._store = store or _FirestoreSessionStore()
        self._cache = {}

    def create(self, email):
        token = secrets.token_urlsafe(32)
        expires_at = time.time() + SESSION_TTL_DAYS * 86400
        self._store.save(token, email, expires_at)
        self._cache[token] = email
        return token

    def email_for(self, token):
        email = self._cache.get(token)
        if email:
            return email
        data = self._store.get(token)
        if not data:
            return None
        expires_at = data.get("expires_at") or 0
        if time.time() >= expires_at:
            self._store.delete(token)
            return None
        email = data.get("email")
        if email:
            self._cache[token] = email
        return email

    def destroy(self, token):
        self._cache.pop(token, None)
        self._store.delete(token)

    def update_email(self, token, new_email):
        if token in self._cache:
            self._cache[token] = new_email
        data = self._store.get(token)
        if data:
            self._store.save(token, new_email, data.get("expires_at") or time.time())