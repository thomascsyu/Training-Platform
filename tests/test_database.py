import asyncio
import importlib
import sys

import pytest


class FakeMotorDatabase:
    def __init__(self, name):
        self.name = name
        self.users = object()

    def __getitem__(self, name):
        return f"collection:{name}"


class FakeMotorClient:
    instances = []

    def __init__(self, *args, **kwargs):
        self.args = args
        self.kwargs = kwargs
        self.closed = False
        FakeMotorClient.instances.append(self)

    def __getitem__(self, name):
        return FakeMotorDatabase(name)

    def close(self):
        self.closed = True


@pytest.fixture(autouse=True)
def restore_database_modules():
    original_config = sys.modules.get("config")
    original_database = sys.modules.get("database")
    yield
    sys.modules.pop("database", None)
    sys.modules.pop("config", None)
    if original_database is not None:
        sys.modules["database"] = original_database
    if original_config is not None:
        sys.modules["config"] = original_config
    FakeMotorClient.instances.clear()


def import_database(monkeypatch):
    monkeypatch.setenv("MONGO_URL", "mongodb://lazy-client:27017")
    monkeypatch.setenv("DB_NAME", "learnhub_lazy_test")
    monkeypatch.setenv("JWT_SECRET", "test-jwt-secret-for-pytest-only-32b")
    sys.modules.pop("database", None)
    sys.modules.pop("config", None)
    return importlib.import_module("database")


def test_database_import_does_not_create_client(monkeypatch):
    database = import_database(monkeypatch)
    monkeypatch.setattr(database, "AsyncIOMotorClient", FakeMotorClient)

    assert FakeMotorClient.instances == []


def test_database_client_is_created_on_first_db_use(monkeypatch):
    database = import_database(monkeypatch)
    monkeypatch.setattr(database, "AsyncIOMotorClient", FakeMotorClient)

    assert database.db.users is database.db.users
    assert database.db["courses"] == "collection:courses"

    assert len(FakeMotorClient.instances) == 1
    assert FakeMotorClient.instances[0].args == ("mongodb://lazy-client:27017",)
    assert FakeMotorClient.instances[0].kwargs == {"serverSelectionTimeoutMS": 5000}


def test_close_db_client_closes_and_resets_lazy_client(monkeypatch):
    database = import_database(monkeypatch)
    monkeypatch.setattr(database, "AsyncIOMotorClient", FakeMotorClient)

    _ = database.db.users
    client = FakeMotorClient.instances[0]

    asyncio.run(database.close_db_client())

    assert client.closed is True
    _ = database.db.users
    assert len(FakeMotorClient.instances) == 2
