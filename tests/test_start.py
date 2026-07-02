import start


def test_resolve_log_level_defaults_to_info(monkeypatch):
    monkeypatch.delenv("LOG_LEVEL", raising=False)
    assert start._resolve_log_level() == "info"


def test_resolve_log_level_accepts_valid_values_case_insensitively(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "DEBUG")
    assert start._resolve_log_level() == "debug"

    monkeypatch.setenv("LOG_LEVEL", "Warning")
    assert start._resolve_log_level() == "warning"

    monkeypatch.setenv("LOG_LEVEL", "ERROR")
    assert start._resolve_log_level() == "error"


def test_resolve_log_level_maps_warn_to_warning(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "warn")
    assert start._resolve_log_level() == "warning"

    monkeypatch.setenv("LOG_LEVEL", "WARN")
    assert start._resolve_log_level() == "warning"


def test_resolve_log_level_falls_back_on_invalid_or_blank(monkeypatch):
    monkeypatch.setenv("LOG_LEVEL", "verbose")
    assert start._resolve_log_level() == "info"

    monkeypatch.setenv("LOG_LEVEL", "")
    assert start._resolve_log_level() == "info"


def test_resolve_host_overrides_loopback_addresses(monkeypatch):
    monkeypatch.setenv("HOST", "LocalHost")
    assert start._resolve_host() == "0.0.0.0"

    monkeypatch.setenv("HOST", "127.0.0.1")
    assert start._resolve_host() == "0.0.0.0"

    monkeypatch.setenv("HOST", "::1")
    assert start._resolve_host() == "0.0.0.0"


def test_resolve_host_preserves_non_loopback_address(monkeypatch):
    monkeypatch.setenv("HOST", "0.0.0.0")
    assert start._resolve_host() == "0.0.0.0"

    monkeypatch.setenv("HOST", "192.168.1.1")
    assert start._resolve_host() == "192.168.1.1"

    monkeypatch.delenv("HOST", raising=False)
    assert start._resolve_host() == "0.0.0.0"


def test_parse_port_falls_back_on_invalid_or_out_of_range(monkeypatch):
    monkeypatch.setenv("PORT", "bad")
    assert start._parse_port() == 8080

    monkeypatch.setenv("PORT", "70000")
    assert start._parse_port() == 8080

    monkeypatch.setenv("PORT", "-1")
    assert start._parse_port() == 8080


def test_parse_port_trims_whitespace(monkeypatch):
    monkeypatch.setenv("PORT", " 8085 ")
    assert start._parse_port() == 8085
