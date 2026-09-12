"""Regras de validação de email e senha."""
import re

EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
MIN_PASSWORD_LENGTH = 8


def normalize_email(email):
    return (email or "").strip().lower()


def is_valid_email(email):
    return bool(EMAIL_RE.match(email))


def is_valid_password(password):
    return len(password) >= MIN_PASSWORD_LENGTH