import faulthandler
import ipaddress
import os
import sys
import traceback

# Emit before third-party imports so Zeabur logs show activity even if a
# native extension segfaults during import (faulthandler is not enabled yet).
print("[learnhub-startup] boot", file=sys.stderr, flush=True)
faulthandler.enable(file=sys.stderr, all_threads=True)

import uvicorn
from uvicorn.config import LOG_LEVELS


def _log(message: str) -> None:
    print(f"[learnhub-startup] {message}", file=sys.stderr, flush=True)


def _parse_port() -> int:
    raw_port = (os.environ.get("PORT") or "8080").strip()
    try:
        port = int(raw_port)
    except (TypeError, ValueError):
        _log(f"Invalid PORT value {raw_port!r}; falling back to 8080")
        return 8080

    if not 0 < port < 65536:
        _log(f"Invalid PORT value {raw_port!r}; falling back to 8080")
        return 8080

    return port


_VALID_LOG_LEVELS = set(LOG_LEVELS.keys())


def _resolve_host() -> str:
    raw_host = (os.environ.get("HOST") or "0.0.0.0").strip()
    if not raw_host:
        return "0.0.0.0"

    host = raw_host.lower()
    if host == "localhost":
        _log(
            f"HOST={raw_host!r} is not reachable from outside the container; using 0.0.0.0"
        )
        return "0.0.0.0"

    try:
        parsed_host = ipaddress.ip_address(raw_host)
    except ValueError:
        _log(
            f"HOST={raw_host!r} is not a bindable IP address; using 0.0.0.0"
        )
        return "0.0.0.0"

    if parsed_host.is_loopback:
        _log(
            f"HOST={raw_host!r} is not reachable from outside the container; using 0.0.0.0"
        )
        return "0.0.0.0"

    return raw_host


def _resolve_log_level() -> str:
    raw = (os.environ.get("LOG_LEVEL") or "info").strip()
    if not raw:
        return "info"
    level = raw.lower()
    if level == "warn":
        level = "warning"
    if level not in _VALID_LOG_LEVELS:
        _log(f"Invalid LOG_LEVEL value {raw!r}; falling back to 'info'")
        return "info"
    return level


def main() -> None:
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    host = _resolve_host()
    port = _parse_port()
    log_level = _resolve_log_level()
    _log(f"Starting LearnHub API on {host}:{port}")

    try:
        from server import app
    except Exception:
        _log("Application import failed before Uvicorn startup")
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)

    uvicorn.run(app, host=host, port=port, log_level=log_level)


if __name__ == "__main__":
    main()
