"""Persistência no Firestore.

users/{email}      -> credenciais (salt, password_hash, created_at)
user_data/{email}  -> dados financeiros (recurrences, oneOffs)
sessions/{token}   -> sessões persistentes (email, expires_at)

Mantidas em coleções separadas para que o caminho de escrita das transações
financeiras nunca encoste nos campos de senha.

Implementa a interface de Store usada pelos domínios; testes usam um
FakeStore em memória com as mesmas assinaturas.

A credencial da SA sai do Secret Manager (env FINANCAS_SA_SECRET) quando
definida; caso contrário usa as Application Default Credentials (ex. local ou
GOOGLE_APPLICATION_CREDENTIALS), mantendo compatibilidade com dev/teste.
"""
import json
import os

from google.cloud import firestore


def _sa_credentials(secret_client=None):
    secret_name = os.environ.get("FINANCAS_SA_SECRET")
    if not secret_name:
        return None
    from google.auth import default
    from google.oauth2.service_account import Credentials

    if secret_client is None:
        from google.cloud import secretmanager

        bootstrap, _ = default(scopes=["https://www.googleapis.com/auth/cloud-platform"])
        secret_client = secretmanager.SecretManagerServiceClient(credentials=bootstrap)
    response = secret_client.access_secret_version(name=secret_name)
    payload = response.payload.data.decode("utf-8")
    return Credentials.from_service_account_info(json.loads(payload))


class FirestoreStore:
    def __init__(self):
        self._client = None

    def _get_client(self):
        if self._client is None:
            self._client = firestore.Client(credentials=_sa_credentials())
        return self._client

    # users

    def list_user_emails(self):
        docs = self._get_client().collection("users").stream()
        return [doc.id for doc in docs]

    def get_user_auth(self, email):
        doc = self._get_client().collection("users").document(email).get()
        return doc.to_dict() if doc.exists else None

    def save_user_auth(self, email, data):
        self._get_client().collection("users").document(email).set(data)

    def update_password(self, email, salt, password_hash):
        self._get_client().collection("users").document(email).update({
            "salt": salt,
            "password_hash": password_hash,
        })

    # user_data

    def get_user_data(self, email):
        doc = self._get_client().collection("user_data").document(email).get()
        return doc.to_dict() if doc.exists else None

    def save_user_data(self, email, data):
        self._get_client().collection("user_data").document(email).set(data)

    # rename (atomico: users + user_data)

    def rename_user(self, old_email, new_email):
        client = self._get_client()

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

    # sessions

    def save_session(self, token, email, expires_at):
        self._get_client().collection("sessions").document(token).set({
            "email": email,
            "expires_at": expires_at,
        })

    def get_session(self, token):
        doc = self._get_client().collection("sessions").document(token).get()
        return doc.to_dict() if doc.exists else None

    def list_sessions(self, email):
        docs = self._get_client().collection("sessions").where("email", "==", email).stream()
        return [doc.id for doc in docs]

    def delete_session(self, token):
        self._get_client().collection("sessions").document(token).delete()


default_store = FirestoreStore()