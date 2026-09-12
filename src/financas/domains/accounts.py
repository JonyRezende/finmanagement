"""Domínio de conta: troca de senha e email."""
from ..errors import Error
from ..services import password, rules


class AccountsService:
    def __init__(self, store, sessions):
        self._store = store
        self._sessions = sessions

    def change_password(self, email, current_password, new_password, token=None):
        user = self._store.get_user_auth(email)
        if not user or not password.verify_password(current_password, user["salt"], user["password_hash"]):
            raise Error("Senha atual incorreta", status=401)
        if not rules.is_valid_password(new_password):
            raise Error("A nova senha deve ter entre 8 e 256 caracteres")

        salt, password_hash = password.hash_password(new_password)
        self._store.update_password(email, salt, password_hash)
        if token:
            self._sessions.destroy_for_email(email, except_token=token)

    def change_email(self, email, token, current_password, new_email):
        new_email = rules.normalize_email(new_email)

        user = self._store.get_user_auth(email)
        if not user or not password.verify_password(current_password, user["salt"], user["password_hash"]):
            raise Error("Senha atual incorreta", status=401)
        if not rules.is_valid_email(new_email):
            raise Error("Email inválido")
        if new_email == email:
            raise Error("O novo email deve ser diferente do atual")
        if self._store.get_user_auth(new_email):
            raise Error("Email já cadastrado", status=409)

        self._store.rename_user(email, new_email)
        if token:
            self._sessions.update_email(token, new_email)
        self._sessions.destroy_for_email(email)
        return new_email