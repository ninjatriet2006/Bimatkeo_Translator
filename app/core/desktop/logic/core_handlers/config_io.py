"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.config_io
- RESPONSIBILITY: Proxy configuration file IO operations.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.config_io.paths, app.core.desktop.logic.config_io.yaml_io
- IN = OUT: Resolves paths and saves yaml data for the app.
=============================================================================
"""

class ConfigIOHandlersMixin:
    def _get_yaml_config_path(self, filename: str) -> str:
        from app.core.desktop.logic.config_io.paths import get_yaml_config_path
        return get_yaml_config_path(self.project_base_dir, filename)

    def _save_yaml_config(self, filename: str, data: dict, wrap_key: str = None):
        from app.core.desktop.logic.config_io.yaml_io import save_yaml_config
        save_yaml_config(self.project_base_dir, filename, data, wrap_key)
