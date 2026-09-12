import pytest

from src.financas.domains import finance as finance_domain
from src.financas.errors import Error
from tests.fakes import FakeStore


def make_finance():
    return finance_domain.FinanceService(FakeStore())


def test_get_data_defaults_to_empty():
    svc = make_finance()
    assert svc.get_data("a@b.com") == {"recurrences": [], "oneOffs": []}


def test_save_and_read_roundtrip():
    svc = make_finance()
    payload = {"recurrences": [{"id": "r1"}], "oneOffs": [{"id": "o1"}]}
    svc.save_data("a@b.com", payload)
    assert svc.get_data("a@b.com") == payload


def test_rejects_non_list_fields():
    svc = make_finance()
    with pytest.raises(Error):
        svc.save_data("a@b.com", {"recurrences": "nao-lista", "oneOffs": []})