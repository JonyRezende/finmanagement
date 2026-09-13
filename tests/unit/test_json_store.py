from src.financas.infra.json_store import JsonStore


def make_store(tmp_path):
    return JsonStore(str(tmp_path / "db.json"))


def test_auth_and_data_roundtrip(tmp_path):
    store = make_store(tmp_path)
    assert store.get_user_auth("a@b.com") is None
    store.save_user_auth("a@b.com", {"email": "a@b.com", "salt": "s", "password_hash": "h", "created_at": 1})
    store.save_user_data("a@b.com", {"recurrences": [], "oneOffs": []})
    assert store.get_user_auth("a@b.com")["salt"] == "s"
    assert store.get_user_data("a@b.com") == {"recurrences": [], "oneOffs": []}
    assert store.get_user_data("outro@b.com") is None


def test_update_password(tmp_path):
    store = make_store(tmp_path)
    store.save_user_auth("a@b.com", {"email": "a@b.com", "salt": "s", "password_hash": "h", "created_at": 1})
    store.update_password("a@b.com", "novo-salt", "novo-hash")
    user = store.get_user_auth("a@b.com")
    assert user["salt"] == "novo-salt"
    assert user["password_hash"] == "novo-hash"


def test_persists_across_instances(tmp_path):
    path = str(tmp_path / "db.json")
    JsonStore(path).save_user_auth("a@b.com", {"email": "a@b.com", "salt": "s", "password_hash": "h", "created_at": 1})
    JsonStore(path).save_user_data("a@b.com", {"recurrences": [], "oneOffs": []})
    again = JsonStore(path)
    assert again.get_user_auth("a@b.com")["salt"] == "s"
    assert again.get_user_data("a@b.com")["recurrences"] == []


def test_list_user_emails(tmp_path):
    store = make_store(tmp_path)
    assert store.list_user_emails() == []
    store.save_user_auth("a@b.com", {"email": "a@b.com", "salt": "s", "password_hash": "h", "created_at": 1})
    store.save_user_auth("c@d.com", {"email": "c@d.com", "salt": "s", "password_hash": "h", "created_at": 1})
    assert set(store.list_user_emails()) == {"a@b.com", "c@d.com"}


def test_rename_user_moves_auth_and_data(tmp_path):
    store = make_store(tmp_path)
    store.save_user_auth("a@b.com", {"email": "a@b.com", "salt": "s", "password_hash": "h", "created_at": 1})
    store.save_user_data("a@b.com", {"recurrences": [], "oneOffs": []})
    store.rename_user("a@b.com", "novo@b.com")
    assert store.get_user_auth("a@b.com") is None
    assert store.get_user_data("a@b.com") is None
    assert store.get_user_auth("novo@b.com")["salt"] == "s"
    assert store.get_user_data("novo@b.com")["recurrences"] == []


def test_sessions(tmp_path):
    store = make_store(tmp_path)
    store.save_session("token1", "a@b.com", 1000)
    store.save_session("token2", "a@b.com", 2000)
    store.save_session("token3", "c@d.com", 3000)
    assert store.get_session("token1") == {"email": "a@b.com", "expires_at": 1000}
    assert set(store.list_sessions("a@b.com")) == {"token1", "token2"}
    store.delete_session("token1")
    assert store.get_session("token1") is None
    assert store.list_sessions("a@b.com") == ["token2"]


def _clear_gcp_env(monkeypatch):
    monkeypatch.delenv("FINANCAS_SA_SECRET", raising=False)
    monkeypatch.delenv("GOOGLE_APPLICATION_CREDENTIALS", raising=False)
    monkeypatch.delenv("FINANCAS_STORAGE", raising=False)
    monkeypatch.setenv("FINANCAS_DB", "/tmp/opencode-test-db.json")


def test_default_store_is_local_without_gcp(monkeypatch):
    from src.financas.app import make_default_store

    _clear_gcp_env(monkeypatch)
    assert make_default_store().__class__.__name__ == "JsonStore"


def test_default_store_is_firestore_with_secret(monkeypatch):
    from src.financas.app import make_default_store

    _clear_gcp_env(monkeypatch)
    monkeypatch.setenv("FINANCAS_SA_SECRET", "projects/x/secrets/y/versions/latest")
    assert make_default_store().__class__.__name__ == "FirestoreStore"


def test_forced_local_beats_gcp_secret(monkeypatch):
    from src.financas.app import make_default_store

    _clear_gcp_env(monkeypatch)
    monkeypatch.setenv("FINANCAS_SA_SECRET", "projects/x/secrets/y/versions/latest")
    monkeypatch.setenv("FINANCAS_STORAGE", "local")
    assert make_default_store().__class__.__name__ == "JsonStore"


def test_forced_firestore_without_gcp(monkeypatch):
    from src.financas.app import make_default_store

    _clear_gcp_env(monkeypatch)
    monkeypatch.setenv("FINANCAS_STORAGE", "firestore")
    assert make_default_store().__class__.__name__ == "FirestoreStore"