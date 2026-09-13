import base64

import pytest

from src.financas.domains import finance as finance_domain
from src.financas.errors import Error
from tests.fakes import FakeStore


class _FakeKeyProvider:
    def __init__(self, key):
        self._key = key

    def get_master_key(self):
        return self._key


def make_finance():
    return finance_domain.FinanceService(FakeStore(), key_provider=_FakeKeyProvider(bytes(range(32))))


def test_get_data_defaults_to_empty():
    svc = make_finance()
    assert svc.get_data("a@b.com") == {"recurrences": [], "oneOffs": []}


def test_save_and_read_roundtrip():
    svc = make_finance()
    payload = {"recurrences": [{"id": "r1"}], "oneOffs": [{"id": "o1"}]}
    svc.save_data("a@b.com", payload)
    assert svc.get_data("a@b.com") == payload


def test_saves_encrypted_blob():
    svc = make_finance()
    svc.save_data("a@b.com", {"recurrences": [{"id": "r1"}], "oneOffs": []})
    stored = svc._store.get_user_data("a@b.com")
    assert stored.get("v") == 2
    raw = " ".join(stored["data"].values())
    assert "r1" not in raw
    assert "recurrences" not in raw


def test_reads_legacy_plaintext():
    svc = make_finance()
    svc._store.save_user_data("a@b.com", {"recurrences": [{"id": "r1"}], "oneOffs": []})
    assert svc.get_data("a@b.com") == {"recurrences": [{"id": "r1"}], "oneOffs": []}


def test_tampered_blob_raises():
    svc = make_finance()
    svc.save_data("a@b.com", {"recurrences": [{"id": "r1"}], "oneOffs": []})
    stored = svc._store.get_user_data("a@b.com")
    ct = bytearray(base64.b64decode(stored["data"]["ct"]))
    ct[-1] ^= 0x01
    stored["data"]["ct"] = base64.b64encode(bytes(ct)).decode("ascii")
    svc._store.save_user_data("a@b.com", stored)
    with pytest.raises(Error):
        svc.get_data("a@b.com")


def test_rejects_non_list_fields():
    svc = make_finance()
    with pytest.raises(Error):
        svc.save_data("a@b.com", {"recurrences": "nao-lista", "oneOffs": []})