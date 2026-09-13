import base64
import json

import pytest

from src.financas.errors import Error
from src.financas.services import crypto


def _key():
    return bytes(range(32))


def _flip_last(raw_b64):
    payload = bytearray(base64.b64decode(raw_b64))
    payload[-1] ^= 0x01
    return base64.b64encode(bytes(payload)).decode("ascii")


def test_encrypt_decrypt_roundtrip():
    key = _key()
    payload = {"recurrences": [{"amount": 2000}], "oneOffs": []}
    envelope = crypto.encrypt_json(key, payload)
    assert envelope["v"] == 2
    assert crypto.decrypt_json(key, envelope) == payload


def test_plaintext_not_legible_in_envelope():
    key = _key()
    payload = {"recurrences": [{"description": "salario-secreto", "amount": 2000}], "oneOffs": []}
    envelope = crypto.encrypt_json(key, payload)
    raw = " ".join(envelope["data"].values())
    assert "salario-secreto" not in raw
    assert "recurrences" not in raw
    assert json.dumps(payload) not in raw


def test_wrong_key_fails():
    k1 = _key()
    k2 = bytes(reversed(range(32)))
    envelope = crypto.encrypt_json(k1, {"a": 1})
    with pytest.raises(Error):
        crypto.decrypt_json(k2, envelope)


def test_tampered_ciphertext_fails():
    key = _key()
    envelope = crypto.encrypt_json(key, {"a": 1})
    envelope["data"]["ct"] = _flip_last(envelope["data"]["ct"])
    with pytest.raises(Error):
        crypto.decrypt_json(key, envelope)


def test_tampered_tag_fails():
    key = _key()
    envelope = crypto.encrypt_json(key, {"a": 1})
    envelope["data"]["tag"] = _flip_last(envelope["data"]["tag"])
    with pytest.raises(Error):
        crypto.decrypt_json(key, envelope)


def test_malformed_envelope_fails():
    key = _key()
    with pytest.raises(Error):
        crypto.decrypt_json(key, {"data": {}})
    with pytest.raises(Error):
        crypto.decrypt_json(key, {})


def test_user_keys_differ_and_are_deterministic():
    master = _key()
    assert crypto.derive_user_key(master, "a@b.com") == crypto.derive_user_key(master, "a@b.com")
    assert crypto.derive_user_key(master, "a@b.com") != crypto.derive_user_key(master, "c@b.com")


def test_is_encrypted():
    assert crypto.is_encrypted({"v": 2, "data": {}})
    assert not crypto.is_encrypted({"recurrences": []})
    assert not crypto.is_encrypted(None)