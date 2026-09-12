"""Domínio de autenticação: register/login/logout e sessão."""
import time

from ..errors import Error
from ..services import rate_limit, rules
from ..services import password as pwd
from ..services.sessions import SessionService


class AuthService:
    def __init__(self, store):
        self._store = store
        self.sessions = SessionService(store)

    def register(self, email, password, password_confirm):
        email = rules.normalize_email(email)
        if not rules.is_valid_email(email):
            raise Error("Email inválido")
        if not rules.is_valid_password(password):
            raise Error("Senha deve ter ao menos 8 caracteres")
        if password != password_confirm:
            raise Error("As senhas não coincidem")
        if self._store.get_user_auth(email):
            raise Error("Email já cadastrado", status=409)

        salt, password_hash = pwd.hash_password(password)
        self._store.save_user_auth(email, {
            "email": email,
            "salt": salt,
            "password_hash": password_hash,
            "created_at": time.time(),
        })
        self._store.save_user_data(email, {"recurrences": [], "oneOffs": []})
        return self.sessions.create(email)

    def login(self, email, password):
        email = rules.normalize_email(email)
        if rate_limit.is_blocked(email):
            raise Error("Muitas tentativas. Tente novamente em instantes.", status=429)

        user = self._store.get_user_auth(email)
        if not user or not pwd.verify_password(password, user["salt"], user["password_hash"]):
            rate_limit.register_failure(email)
            raise Error("Email ou senha inválidos", status=401)

        rate_limit.register_success(email)
        return self.sessions.create(email)

    def logout(self, token):
        self.sessions.destroy(token)

    def email_for(self, token):
        return self.sessions.email_for(token)