import pytest

from src.financas.services import rules


def test_normalize_email():
    assert rules.normalize_email("  A@B.COM ") == "a@b.com"


@pytest.mark.parametrize("email", [
    "a@b.com",
    "jonathas.rezende@gmail.com",
    "a.b+c@x.io",
])
def test_valid_emails(email):
    assert rules.is_valid_email(email)