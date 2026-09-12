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


def update_password(email, salt, password_hash):
    _get_client().collection("users").document(email).update({
        "salt": salt,
        "password_hash": password_hash,
    })


def rename_user(old_email, new_email):
    client = _get_client()

    @firestore.transactional
    def move_user(transaction):
        users = client.collection("users")
        data = client.collection("user_data")
        auth_ref = users.document(old_email)
        data_ref = data.document(old_email)
        auth_doc = auth_ref.get(transaction=transaction)
        data_doc = data_ref.get(transaction=transaction)
        if auth_doc.exists:
            transaction.set(users.document(new_email), auth_doc.to_dict())
            transaction.delete(auth_ref)
        if data_doc.exists:
            transaction.set(data.document(new_email), data_doc.to_dict())
            transaction.delete(data_ref)

    move_user(client.transaction())


def save_session(token, email, expires_at):
    _get_client().collection("sessions").document(token).set({
        "email": email,
        "expires_at": expires_at,
    })


def get_session(token):
    doc = _get_client().collection("sessions").document(token).get()
    return doc.to_dict() if doc.exists else None


def delete_session(token):
    _get_client().collection("sessions").document(token).delete()
