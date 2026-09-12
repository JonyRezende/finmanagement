"""Autenticação simples: hash de senha, sessões em memória e rate limit de login."""
import hashlib
import hmac
import os
import re
import secrets
import time

import firestore_client

PBKDF2_ITERATIONS = 200_000
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

SESSIONS = {}  # token -> email

_LOGIN_ATTEMPTS = {}  # email -> (failed_count, blocked_until_ts)
MAX_ATTEMPTS = 5
BLOCK_SECONDS = 60


def normalize_email(email):
    return (email or "").strip().lower()


def is_valid_email(email):
    return bool(EMAIL_RE.match(email))


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt.hex(), digest.hex()


def verify_password(password, salt_hex, hash_hex):
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), hash_hex)


def create_session(email):
    token = secrets.token_urlsafe(32)
    SESSIONS[token] = email
    return token


def get_session_email(token):
    return SESSIONS.get(token)


def destroy_session(token):
    SESSIONS.pop(token, None)


def is_login_blocked(email):
    failed_count, blocked_until = _LOGIN_ATTEMPTS.get(email, (0, 0))
    return time.time() < blocked_until


def register_login_failure(email):
    failed_count, _ = _LOGIN_ATTEMPTS.get(email, (0, 0))
    failed_count += 1
    blocked_until = time.time() + BLOCK_SECONDS if failed_count >= MAX_ATTEMPTS else 0
    _LOGIN_ATTEMPTS[email] = (failed_count, blocked_until)


def register_login_success(email):
    _LOGIN_ATTEMPTS.pop(email, None)
