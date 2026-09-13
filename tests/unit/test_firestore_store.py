from src.financas.infra.firestore import FirestoreStore


class FakeCollection:
    def __init__(self, ids):
        self._ids = ids

    def stream(self):
        return [type("Doc", (), {"id": i})() for i in self._ids]


class FakeFirestoreClient:
    def __init__(self, users):
        self._users = users

    def collection(self, name):
        assert name == "users"
        return FakeCollection(self._users)


def test_list_user_emails():
    store = FirestoreStore()
    store._client = FakeFirestoreClient(["a@b.com", "c@d.com"])
    assert set(store.list_user_emails()) == {"a@b.com", "c@d.com"}