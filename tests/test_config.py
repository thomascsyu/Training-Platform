import importlib
import sys

import pytest


@pytest.fixture(autouse=True)
def restore_config_module():
    original_config = sys.modules.get("config")
    yield
    sys.modules.pop("config", None)
    if original_config is not None:
        sys.modules["config"] = original_config


def load_config(monkeypatch, **env):
    for name in (
        "MONGO_URL",
        "MONGODB_URI",
        "MONGO_URI",
        "MONGO_CONNECTION_STRING",
        "DB_NAME",
        "JWT_SECRET",
    ):
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
        MONGO_URI="mongodb://fallback-uri:27017",
        MONGO_CONNECTION_STRING="mongodb://fallback-connection:27017",
    )

    assert config.MONGO_URL == "mongodb://primary:27017"


@pytest.mark.parametrize(
    ("env_name", "mongo_url"),
    [
        ("MONGODB_URI", "mongodb://zeabur-mongodb-uri:27017"),
        ("MONGO_URI", "mongodb://zeabur-mongo-uri:27017"),
        ("MONGO_CONNECTION_STRING", "mongodb://zeabur-connection:27017"),
    ],
)
def test_mongo_url_falls_back_to_common_zeabur_names(
    monkeypatch, env_name, mongo_url
):
    config = load_config(monkeypatch, **{env_name: mongo_url})

    assert config.MONGO_URL == mongo_url
