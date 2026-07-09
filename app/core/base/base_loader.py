"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base.base_loader
- RESPONSIBILITY: Defines BaseConfigLoader class providing utilities for schema and config file processing.
- CALLED BY: app.core.base, app.core.config_loader, desktop_ui.config.loader
- CALLS TO: app.core.base.io, app.core.base.schema_loader, app.core.base.parser
- IN = OUT: Defines abstract BaseConfigLoader class.
=============================================================================
"""
import os
from typing import Any

from .io import load_yaml_file, save_yaml_file
from .schema_loader import load_backend_schema, parse_schema_output, strip_ansi
from .parser import get_definition_from_ref, get_flat_properties, parse_factory_defaults

class BaseConfigLoader:
    project_base_dir: str
    cache_path: str
    backend_schema: dict[str, Any] | None
    factory_defaults: dict[str, Any]

    def _save_yaml_file(self, path: str, data: Any) -> None:
        return save_yaml_file(path, data)

    def _load_yaml_file(self, path: str) -> dict[str, Any]:
        return load_yaml_file(path)

    def _load_backend_schema(self):
        fallback_path = os.path.join(self.project_base_dir, ".config", "configs", "schema_fallback.yaml")
        return load_backend_schema(getattr(self, "cache_path", ""), fallback_path)

    def _parse_schema_output(self, stdout: str):
        return parse_schema_output(stdout)

    def _strip_ansi(self, text: str):
        return strip_ansi(text)

    def _get_definition_from_ref(self, ref_path: str):
        return get_definition_from_ref(self.backend_schema or {}, ref_path)

    def _get_flat_properties(self) -> dict[str, Any]:
        return get_flat_properties(self.backend_schema or {})

    def _parse_factory_defaults(self):
        return parse_factory_defaults(self.backend_schema or {})

    def get_factory_defaults(self):
        return getattr(self, "factory_defaults", {})

    def get_tab_order(self):
        ui_map = getattr(self, "ui_map", {})
        return list(ui_map.keys())
