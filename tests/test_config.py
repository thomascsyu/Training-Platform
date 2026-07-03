import config


def test_mongo_url_prefers_explicit_mongo_url(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb://primary:27017")
    monkeypatch.setenv("MONGODB_URI", "mongodb://alias:27017")

    assert config._get_mongo_url() == "mongodb://primary:27017"


def test_mongo_url_falls_back_to_mongodb_uri(monkeypatch):
    for name in config._MONGO_URL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("MONGODB_URI", "mongodb://zeabur:27017")

    assert config._get_mongo_url() == "mongodb://zeabur:27017"


def test_mongo_url_falls_back_to_zeabur_connection_string(monkeypatch):
    for name in config._MONGO_URL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("MONGO_CONNECTION_STRING", "mongodb://mongo.zeabur.internal:27017")

    assert config._get_mongo_url() == "mongodb://mongo.zeabur.internal:27017"


def test_mongo_url_falls_back_to_mongo_uri(monkeypatch):
    for name in config._MONGO_URL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    monkeypatch.setenv("MONGO_URI", "mongodb://emergent:27017")

    assert config._get_mongo_url() == "mongodb://emergent:27017"


def test_mongo_url_priority_prefers_earlier_vars(monkeypatch):
    monkeypatch.setenv("MONGODB_URI", "mongodb://second:27017")
    monkeypatch.setenv("MONGO_CONNECTION_STRING", "mongodb://third:27017")
    monkeypatch.setenv("MONGO_URI", "mongodb://fourth:27017")
    monkeypatch.delenv("MONGO_URL", raising=False)

    # MONGODB_URI wins over the later variants
    assert config._get_mongo_url() == "mongodb://second:27017"


def test_mongo_url_defaults_when_all_unset(monkeypatch):
    for name in config._MONGO_URL_ENV_VARS:
        monkeypatch.delenv(name, raising=False)

    assert config._get_mongo_url() == "mongodb://localhost:27017"


def test_int_env_treats_blank_values_as_unset(monkeypatch):
    monkeypatch.setenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "   ")
    assert config._get_int_env("MONGO_SERVER_SELECTION_TIMEOUT_MS", 5000) == 5000


def test_int_env_falls_back_on_invalid_values(monkeypatch):
    monkeypatch.setenv("MONGO_SERVER_SELECTION_TIMEOUT_MS", "bad")
    assert config._get_int_env("MONGO_SERVER_SELECTION_TIMEOUT_MS", 5000) == 5000
