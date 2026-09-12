"""Rate limit de tentativas de login (em memória, por email)."""
import time

MAX_ATTEMPTS = 5
BLOCK_SECONDS = 60

_ATTEMPTS = {}  # email -> (failed_count, blocked_until_ts)


def is_blocked(email):
    _, blocked_until = _ATTEMPTS.get(email, (0, 0))
    return time.time() < blocked_until


def register_failure(email):
    failed_count, _ = _ATTEMPTS.get(email, (0, 0))
    failed_count += 1
    blocked_until = time.time() + BLOCK_SECONDS if failed_count >= MAX_ATTEMPTS else 0
    _ATTEMPTS[email] = (failed_count, blocked_until)


def register_success(email):
    _ATTEMPTS.pop(email, None)


def reset():
    _ATTEMPTS.clear()