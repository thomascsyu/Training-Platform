import importlib
import os
from contextlib import contextmanager

import config


@contextmanager
def _reloaded_config(**env):
    """Set environment variables, reload config, yield it, then restore."""
    keys = list(env.keys())
    original = {k: os.environ.get(k) for k in keys}
    for k, v in env.items():
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = str(v)
    importlib.reload(config)
    try:
        yield config
    finally:
        for k, v in original.items():
            if v is None:
                os.environ.pop(k, None)
            else:
                os.environ[k] = v
        importlib.reload(config)


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


def test_admin_email_is_normalized():
    assert config._normalize_admin_email("  Admin@LearnHub.COM  ") == "admin@learnhub.com"


def test_get_seeded_admin_accounts_includes_second_admin_when_both_set(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@learnhub.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "password-1")
    monkeypatch.setenv("ADMIN2_EMAIL", "admin2@learnhub.com")
    monkeypatch.setenv("ADMIN2_PASSWORD", "password-2")

    accounts = config.get_seeded_admin_accounts()

    assert len(accounts) == 2
    assert accounts[1] == ("Admin 2", "admin2@learnhub.com", "password-2")


def test_get_seeded_admin_accounts_skips_second_admin_when_incomplete(monkeypatch):
    monkeypatch.setenv("ADMIN_EMAIL", "admin@learnhub.com")
    monkeypatch.setenv("ADMIN_PASSWORD", "password-1")
    monkeypatch.setenv("ADMIN2_EMAIL", "admin2@learnhub.com")
    monkeypatch.delenv("ADMIN2_PASSWORD", raising=False)

    accounts = config.get_seeded_admin_accounts()

    assert len(accounts) == 1


def test_cookie_samesite_defaults_to_lax():
    with _reloaded_config(COOKIE_SAMESITE=None, COOKIE_SECURE="false") as cfg:
        assert cfg.COOKIE_SAMESITE == "lax"


def test_cookie_samesite_invalid_value_falls_back_to_lax():
    with _reloaded_config(COOKIE_SAMESITE="invalid", COOKIE_SECURE="false") as cfg:
        assert cfg.COOKIE_SAMESITE == "lax"


def test_cookie_samesite_none_forces_secure():
    with _reloaded_config(COOKIE_SAMESITE="none", COOKIE_SECURE="false") as cfg:
        assert cfg.COOKIE_SAMESITE == "none"
        assert cfg.COOKIE_SECURE is True


def test_cors_origins_default_to_frontend_url():
    with _reloaded_config(
        CORS_ORIGINS=None, FRONTEND_URL="http://example.com"
    ) as cfg:
        assert cfg.CORS_ORIGINS == ["http://example.com"]
        assert cfg.CORS_ALLOW_CREDENTIALS is True


def test_cors_origins_star_disables_credentials():
    with _reloaded_config(CORS_ORIGINS="*") as cfg:
        assert cfg.CORS_ORIGINS == ["*"]
        assert cfg.CORS_ALLOW_CREDENTIALS is False


def test_cors_origins_splits_multiple_values():
    with _reloaded_config(
        CORS_ORIGINS="http://a.com, http://b.com", FRONTEND_URL="http://example.com"
    ) as cfg:
        assert cfg.CORS_ORIGINS == ["http://a.com", "http://b.com"]
        assert cfg.CORS_ALLOW_CREDENTIALS is True


def test_cors_origins_ignores_empty_entries():
    with _reloaded_config(
        CORS_ORIGINS="http://a.com,, http://b.com, ", FRONTEND_URL="http://example.com"
    ) as cfg:
        assert cfg.CORS_ORIGINS == ["http://a.com", "http://b.com"]
