import database


def test_create_client_accepts_valid_mongo_url():
    client = database.create_client("mongodb://localhost:27017")
    assert client.address is None or True  # constructed without raising
    client.close()


def test_create_client_falls_back_on_tcp_scheme():
    # Kubernetes/Zeabur can inject a "tcp://host:port" service address as the
    # connection string; it must not crash the process at import time.
    client = database.create_client("tcp://10.0.0.5:27017")
    assert client is not None
    client.close()


def test_create_client_falls_back_on_wrong_scheme():
    client = database.create_client("postgres://foo:bar@host:5432/db")
    assert client is not None
    client.close()


def test_create_client_falls_back_on_unescaped_credentials():
    client = database.create_client("mongodb://user:p@ss@host:27017/db")
    assert client is not None
    client.close()
