import importlib
import sys


def load_config(monkeypatch, **env):
    for name in ("MONGO_URL", "MONGODB_URI", "DB_NAME", "JWT_SECRET"):
        monkeypatch.delenv(name, raising=False)
    for name, value in env.items():
        monkeypatch.setenv(name, value)

    sys.modules.pop("config", None)
    return importlib.import_module("config")


def test_mongo_url_prefers_mongo_url(monkeypatch):
    config = load_config(
        monkeypatch,
        MONGO_URL="mongodb://primary:27017",
        MONGODB_URI="mongodb://fallback:27017",
    )

    assert config.MONGO_URL == "mongodb://primary:27017"


def test_mongo_url_falls_back_to_mongodb_uri(monkeypatch):
    config = load_config(monkeypatch, MONGODB_URI="mongodb://zeabur:27017")

    assert config.MONGO_URL == "mongodb://zeabur:27017"
