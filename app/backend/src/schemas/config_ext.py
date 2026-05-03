"""
Project-specific config extension.

Add app-specific fields by subclassing CoreBackendConfig, then return their
values from ``build_extra()``. The split exists because the schema declares
*shape* (kept required so TS types are non-optional) while ``build_extra()``
provides the *values* the controller passes in. Keys returned must match the
extra fields you defined; FastAPI rejects unknown ones.

After modifying, run ./scripts/_core/convert-models.sh to regenerate frontend
types.

    class BackendConfig(CoreBackendConfig):
        my_custom_flag: bool
        my_max_widgets: int

    def build_extra() -> dict:
        return {"my_custom_flag": True, "my_max_widgets": 42}
"""

from .config import CoreBackendConfig


class BackendConfig(CoreBackendConfig):
    pass


def build_extra() -> dict:
    return {}
