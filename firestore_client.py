"""Cliente Firestore: duas coleções, uma pra auth e outra pra dados financeiros.

users/{email}      -> credenciais (salt, password_hash, created_at)
user_data/{email}  -> dados financeiros (recurrences, oneOffs)

Mantidas em coleções separadas para que o caminho de escrita das transações
financeiras nunca encoste nos campos de senha.
"""
from google.cloud import firestore

_client = None


def _get_client():
    global _client
    if _client is None:
        _client = firestore.Client()
    return _client


def get_user_auth(email):
    doc = _get_client().collection("users").document(email).get()
    return doc.to_dict() if doc.exists else None


def save_user_auth(email, data):
    _get_client().collection("users").document(email).set(data)


def get_user_data(email):
    doc = _get_client().collection("user_data").document(email).get()
    return doc.to_dict() if doc.exists else None


def save_user_data(email, data):
    _get_client().collection("user_data").document(email).set(data)
