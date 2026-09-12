"""Rate limit de tentativas (em memória, por chave: email/IP)."""
import time

MAX_ATTEMPTS = 5
BLOCK_SECONDS = 60
MAX_REGISTER_ATTEMPTS = 10
REGISTER_BLOCK_SECONDS = 300

_ATTEMPTS = {}  # key -> (failed_count, blocked_until_ts)


def is_blocked(*keys):
    return any(time.time() < _ATTEMPTS.get(k, (0, 0))[1] for k in keys if k)


def register_failure(key, max_attempts=MAX_ATTEMPTS, block_seconds=BLOCK_SECONDS):
    failed_count, _ = _ATTEMPTS.get(key, (0, 0))
    failed_count += 1
    blocked_until = time.time() + block_seconds if failed_count >= max_attempts else 0
    _ATTEMPTS[key] = (failed_count, blocked_until)


def register_success(key):
    _ATTEMPTS.pop(key, None)


def reset():
    _ATTEMPTS.clear()