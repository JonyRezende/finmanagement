"""Domínio de autenticação: orquestra os serviços (senha, sessão, rate limit)."""
from ..services import password, rate_limit, rules
from ..services.sessions import SessionService

_session_service = SessionService()

hash_password = password.hash_password
verify_password = password.verify_password
normalize_email = rules.normalize_email
is_valid_email = rules.is_valid_email
is_login_blocked = rate_limit.is_blocked
register_login_failure = rate_limit.register_failure
register_login_success = rate_limit.register_success


def create_session(email):
    return _session_service.create(email)


def get_session_email(token):
    return _session_service.email_for(token)


def destroy_session(token):
    return _session_service.destroy(token)


def update_session_email(token, new_email):
    return _session_service.update_email(token, new_email)