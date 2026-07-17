"""Ensure certificate_settings can boot even if models lacks the update class."""

import importlib
import sys
import types


def test_certificate_settings_falls_back_when_model_missing():
    # Simulate an older models.py that does not export CertificateSettingsUpdate.
    real_models = sys.modules.get("models")
    stub_models = types.ModuleType("models")
    sys.modules["models"] = stub_models
    sys.modules.pop("routers.certificate_settings", None)
    try:
        module = importlib.import_module("routers.certificate_settings")

        assert hasattr(module, "CertificateSettingsUpdate")
        payload = module.CertificateSettingsUpdate(
            id_format="CERT-{year}-{seq:4}",
            default_background="waves",
            default_primary_color="#ABCDEF",
        )
        assert payload.default_primary_color == "#abcdef"
        assert payload.default_background == "waves"
    finally:
        sys.modules.pop("routers.certificate_settings", None)
        if real_models is not None:
            sys.modules["models"] = real_models
        else:
            sys.modules.pop("models", None)
            importlib.import_module("models")
        importlib.import_module("routers.certificate_settings")
