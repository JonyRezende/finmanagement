"""Domínio de autenticação: register/login/logout e sessão."""
import time

from ..errors import Error
from ..services import password as pwd
from ..services import rate_limit, rules
from ..services.sessions import SessionService


class AuthService:
    def __init__(self, store):
        self._store = store
        self.sessions = SessionService(store)

    def register(self, email, password, password_confirm, ip=None):
        email = rules.normalize_email(email)
        if not rules.is_valid_email(email):
            raise Error("Email inválido")
        if not rules.is_valid_password(password):
            raise Error("A senha deve ter entre 8 e 256 caracteres")
        if password != password_confirm:
            raise Error("As senhas não coincidem")
        if ip:
            reg_key = f"reg:{ip}"
            if rate_limit.is_blocked(reg_key):
                raise Error("Muitas contas criadas neste momento. Tente mais tarde.", status=429)
            rate_limit.register_failure(
                reg_key, rate_limit.MAX_REGISTER_ATTEMPTS, rate_limit.REGISTER_BLOCK_SECONDS,
            )
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

    def login(self, email, password, ip=None):
        email = rules.normalize_email(email)
        email_key = f"email:{email}"
        ip_key = f"ip:{ip}" if ip else None
        if rate_limit.is_blocked(email_key, ip_key):
            raise Error("Muitas tentativas. Tente novamente em instantes.", status=429)

        user = self._store.get_user_auth(email)
        valid = bool(user) and pwd.verify_password(password, user["salt"], user["password_hash"])
        if not valid:
            if not user:
                pwd.dummy_verify(password)
            rate_limit.register_failure(email_key)
            if ip_key:
                rate_limit.register_failure(ip_key)
            raise Error("Email ou senha inválidos", status=401)

        rate_limit.register_success(email_key)
        if ip_key:
            rate_limit.register_success(ip_key)
        return self.sessions.create(email)

    def logout(self, token):
        self.sessions.destroy(token)

    def email_for(self, token):
        return self.sessions.email_for(token)