"""Store local em arquivo JSON para desenvolvimento sem dependência do GCP.

Implementa a mesma interface do FirestoreStore; apenas para uso local (dados
ficam em um arquivo ignorado pelo git, ex. financas-local.json). Nunca usar em
produção.
"""
import json
import os
import threading

from .. import config


class JsonStore:
    def __init__(self, path=None):
        self._path = path or config.LOCAL_DB_PATH
        self._lock = threading.Lock()
        self._data = self._load()

    def _load(self):
        data = {"users": {}, "user_data": {}, "sessions": {}}
        if os.path.exists(self._path):
            with open(self._path, "r", encoding="utf-8") as f:
                loaded = json.load(f)
            for key in data:
                if key in loaded:
                    data[key] = loaded[key]
        return data

    def _save(self):
        os.makedirs(os.path.dirname(os.path.abspath(self._path)), exist_ok=True)
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(self._data, f, ensure_ascii=False, indent=2)

    # users

    def list_user_emails(self):
        with self._lock:
            return list(self._data["users"].keys())

    def get_user_auth(self, email):
        with self._lock:
            return self._data["users"].get(email)

    def save_user_auth(self, email, data):
        with self._lock:
            self._data["users"][email] = dict(data)
            self._save()

    def update_password(self, email, salt, password_hash):
        with self._lock:
            self._data["users"][email]["salt"] = salt
            self._data["users"][email]["password_hash"] = password_hash
            self._save()

    # user_data

    def get_user_data(self, email):
        with self._lock:
            return self._data["user_data"].get(email)

    def save_user_data(self, email, data):
        with self._lock:
            self._data["user_data"][email] = dict(data)
            self._save()

    # rename (atômico localmente: um único lock por instância)

    def rename_user(self, old_email, new_email):
        with self._lock:
            if old_email in self._data["users"]:
                self._data["users"][new_email] = self._data["users"].pop(old_email)
            if old_email in self._data["user_data"]:
                self._data["user_data"][new_email] = self._data["user_data"].pop(old_email)
            self._save()

    # sessions

    def save_session(self, token, email, expires_at):
        with self._lock:
            self._data["sessions"][token] = {"email": email, "expires_at": expires_at}
            self._save()

    def get_session(self, token):
        with self._lock:
            return self._data["sessions"].get(token)

    def list_sessions(self, email):
        with self._lock:
            return [token for token, s in self._data["sessions"].items() if s["email"] == email]

    def delete_session(self, token):
        with self._lock:
            self._data["sessions"].pop(token, None)
            self._save()