"""One broken router must not prevent the API package from loading."""

import importlib
import sys
import types


def test_routes_skips_broken_optional_router(monkeypatch):
    real_cert_settings = sys.modules.get("routers.certificate_settings")

    # Module imports, but is missing the expected `router` export.
    broken = types.ModuleType("routers.certificate_settings")
    monkeypatch.setitem(sys.modules, "routers.certificate_settings", broken)

    sys.modules.pop("routes", None)
    try:
        routes = importlib.import_module("routes")
        paths = {
            getattr(route, "path", "")
            for route in routes.api_router.routes
        }
        assert any("login" in path for path in paths)
        assert not any("certificate-settings" in path for path in paths)
    finally:
        sys.modules.pop("routes", None)
        if real_cert_settings is not None:
            sys.modules["routers.certificate_settings"] = real_cert_settings
        else:
            sys.modules.pop("routers.certificate_settings", None)
            importlib.import_module("routers.certificate_settings")
        importlib.import_module("routes")
