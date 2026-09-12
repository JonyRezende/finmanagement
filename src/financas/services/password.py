"""Hash e verificação de senha (PBKDF2)."""
import hashlib
import hmac
import os

PBKDF2_ITERATIONS = 600_000
LEGACY_PBKDF2_ITERATIONS = 200_000


def _digest(password, salt_hex, iterations):
    salt = bytes.fromhex(salt_hex)
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, iterations).hex()


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt.hex(), digest.hex()


def verify_password(password, salt_hex, hash_hex):
    return hmac.compare_digest(_digest(password, salt_hex, PBKDF2_ITERATIONS), hash_hex)


def verify_legacy_password(password, salt_hex, hash_hex):
    return hmac.compare_digest(_digest(password, salt_hex, LEGACY_PBKDF2_ITERATIONS), hash_hex)


def verify_password_current(password, salt_hex, hash_hex):
    """Aceita o formato atual ou o legado (contas criadas antes do hardening)."""
    return verify_password(password, salt_hex, hash_hex) or verify_legacy_password(password, salt_hex, hash_hex)


_DUMMY_SALT, _DUMMY_HASH = hash_password("dummy-password-para-timing")


def dummy_verify(password):
    """Equaliza o tempo de resposta quando o email não existe no login."""
    return verify_password(password, _DUMMY_SALT, _DUMMY_HASH)