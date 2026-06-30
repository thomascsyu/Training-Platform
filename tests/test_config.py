import config


def test_mongo_url_prefers_explicit_mongo_url(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb://primary:27017")
    monkeypatch.setenv("MONGODB_URI", "mongodb://alias:27017")

    assert config._get_mongo_url() == "mongodb://primary:27017"


def test_mongo_url_falls_back_to_mongodb_uri(monkeypatch):
    monkeypatch.delenv("MONGO_URL", raising=False)
    monkeypatch.setenv("MONGODB_URI", "mongodb://zeabur:27017")

    assert config._get_mongo_url() == "mongodb://zeabur:27017"


def test_int_env_treats_blank_values_as_unset(monkeypatch):
    monkeypatch.setenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "   ")
    assert config._get_int_env("MONGO_SERVER_SELECTION_TIMEOUT_MS", 5000) == 5000
