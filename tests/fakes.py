"""FakeStore em memória com a mesma interface do FirestoreStore.

Usado nos testes de domínio e de API (sem rede).
"""


class FakeStore:
    def __init__(self):
        self.users = {}
        self.user_data = {}
        self.sessions = {}

    def get_user_auth(self, email):
        return self.users.get(email)

    def save_user_auth(self, email, data):
        self.users[email] = dict(data)

    def update_password(self, email, salt, password_hash):
        self.users[email]["salt"] = salt
        self.users[email]["password_hash"] = password_hash

    def get_user_data(self, email):
        return self.user_data.get(email)

    def save_user_data(self, email, data):
        self.user_data[email] = dict(data)

    def rename_user(self, old_email, new_email):
        if old_email in self.users:
            self.users[new_email] = self.users.pop(old_email)
        if old_email in self.user_data:
            self.user_data[new_email] = self.user_data.pop(old_email)

    def save_session(self, token, email, expires_at):
        self.sessions[token] = {"email": email, "expires_at": expires_at}

    def get_session(self, token):
        return self.sessions.get(token)

    def delete_session(self, token):
        self.sessions.pop(token, None)