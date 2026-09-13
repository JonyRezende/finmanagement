"""Cifragem autenticada (AES-GCM) e derivação de chave por usuário.

Formato persistido no banco (versão 2 dos documentos de user_data):

    {"v": 2, "data": {"iv": <base64>, "ct": <base64>, "tag": <base64>}}

A chave usada é derivada por usuário (HKDF-SHA256 a partir da chave-mestra),
limitando o impacto caso uma chave seja comprometida.
"""
import base64
import json
import os

from cryptography.exceptions import InvalidTag
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.hkdf import HKDF

from ..errors import Error

NONCE_SIZE = 12
TAG_SIZE = 16
KEY_SIZE = 32  # AES-256
_INFO = b"finpilot:user-data-key:v1"


def derive_user_key(master_key, email):
    """Deriva a chave AES-256 do usuário a partir da chave-mestra."""
    hkdf = HKDF(
        algorithm=hashes.SHA256(),
        length=KEY_SIZE,
        salt=email.encode("utf-8"),
        info=_INFO,
    )
    return hkdf.derive(master_key)


def encrypt_json(key, obj):
    """Cifra um objeto JSON como envelope AES-GCM da versão 2."""
    plaintext = json.dumps(obj, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    nonce = os.urandom(NONCE_SIZE)
    ciphertext = AESGCM(key).encrypt(nonce, plaintext, None)
    ct, tag = ciphertext[:-TAG_SIZE], ciphertext[-TAG_SIZE:]
    return {
        "v": 2,
        "data": {
            "iv": _b64(nonce),
            "ct": _b64(ct),
            "tag": _b64(tag),
        },
    }


def decrypt_json(key, envelope):
    """Decifra um envelope da versão 2, rejeitando dados adulterados/inválidos."""
    data = envelope.get("data")
    if not isinstance(data, dict):
        raise Error("Formato de dados armazenados inválido", status=500)
    try:
        ciphertext = _unb64(data["ct"]) + _unb64(data["tag"])
        plaintext = AESGCM(key).decrypt(_unb64(data["iv"]), ciphertext, None)
        return json.loads(plaintext.decode("utf-8"))
    except (InvalidTag, KeyError, ValueError):
        raise Error("Não foi possível decifrar os dados armazenados", status=500) from None


def _b64(data):
    return base64.b64encode(data).decode("ascii")


def _unb64(raw):
    return base64.b64decode(raw)


def is_encrypted(data):
    return isinstance(data, dict) and data.get("v") == 2