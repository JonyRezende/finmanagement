"""Regras de validação de email e senha."""
MIN_PASSWORD_LENGTH = 8
MAX_PASSWORD_LENGTH = 256


def normalize_email(email):
    return (email or "").strip().lower()


def is_valid_email(email):
    if " " in email or email.count("@") != 1:
        return False
    local, _, domain = str(email).partition("@")
    _, _, tld = domain.rpartition(".")
    return bool(local) and bool(domain) and bool(tld)


def is_valid_password(password):
    return MIN_PASSWORD_LENGTH <= len(password) <= MAX_PASSWORD_LENGTH