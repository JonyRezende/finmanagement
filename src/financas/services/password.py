"""Hash e verificação de senha (PBKDF2)."""
import hashlib
import hmac
import os

PBKDF2_ITERATIONS = 600_000


def hash_password(password):
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return salt.hex(), digest.hex()


def verify_password(password, salt_hex, hash_hex):
    salt = bytes.fromhex(salt_hex)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return hmac.compare_digest(digest.hex(), hash_hex)


_DUMMY_SALT, _DUMMY_HASH = hash_password("dummy-password-para-timing")


def dummy_verify(password):
    """Equaliza o tempo de resposta quando o email não existe no login."""
    return verify_password(password, _DUMMY_SALT, _DUMMY_HASH)