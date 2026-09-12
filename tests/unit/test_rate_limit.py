from src.financas.services import rate_limit


def setup_function(_):
    rate_limit.reset()


def test_not_blocked_initially():
    assert not rate_limit.is_blocked("a@b.com")


def test_blocks_after_max_attempts():
    for _ in range(rate_limit.MAX_ATTEMPTS):
        rate_limit.register_failure("a@b.com")
    assert rate_limit.is_blocked("a@b.com")


def test_success_resets_attempts():
    rate_limit.register_failure("a@b.com")
    rate_limit.register_success("a@b.com")
    for _ in range(rate_limit.MAX_ATTEMPTS - 1):
        rate_limit.register_failure("a@b.com")
    assert not rate_limit.is_blocked("a@b.com")


def test_failures_are_per_email():
    for _ in range(rate_limit.MAX_ATTEMPTS):
        rate_limit.register_failure("a@b.com")
    assert rate_limit.is_blocked("a@b.com")
    assert not rate_limit.is_blocked("outro@b.com")