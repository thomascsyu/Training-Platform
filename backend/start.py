import faulthandler
import os
import sys
import traceback

# Emit before third-party imports so Zeabur logs show activity even if a
# native extension segfaults during import (faulthandler is not enabled yet).
print("[learnhub-startup] boot", file=sys.stderr, flush=True)
faulthandler.enable(file=sys.stderr, all_threads=True)

import uvicorn


def _log(message: str) -> None:
    print(f"[learnhub-startup] {message}", file=sys.stderr, flush=True)


def _parse_port() -> int:
    raw_port = os.environ.get("PORT", "8080")
    try:
        port = int(raw_port)
    except (TypeError, ValueError):
        _log(f"Invalid PORT value {raw_port!r}; falling back to 8080")
        return 8080

    if not 0 < port < 65536:
        _log(f"Invalid PORT value {raw_port!r}; falling back to 8080")
        return 8080

    return port


def main() -> None:
    os.environ.setdefault("PYTHONUNBUFFERED", "1")

    host = os.environ.get("HOST") or "0.0.0.0"
    port = _parse_port()
    _log(f"Starting LearnHub API on {host}:{port}")

    try:
        from server import app
    except Exception:
        _log("Application import failed before Uvicorn startup")
        traceback.print_exc(file=sys.stderr)
        raise SystemExit(1)

    uvicorn.run(app, host=host, port=port, log_level=os.environ.get("LOG_LEVEL", "info"))


if __name__ == "__main__":
    main()
