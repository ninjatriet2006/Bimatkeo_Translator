"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base_config
- RESPONSIBILITY: Expose core base_config components.
- CALLED BY: app.core.config_loader, desktop_ui.config.loader
- CALLS TO: app.core.base_config.base_loader, app.core.base_config.io, app.core.base_config.parser, app.core.base_config.schema_loader
- IN = OUT: Initialization module.
=============================================================================
"""
from .base_loader import BaseConfigLoader
from .io import load_yaml_file, save_yaml_file
from .schema_loader import load_backend_schema, parse_schema_output, strip_ansi
from .parser import get_definition_from_ref, get_flat_properties, parse_factory_defaults

__all__ = [
    "BaseConfigLoader",
    "load_yaml_file",
    "save_yaml_file",
    "load_backend_schema",
    "parse_schema_output",
    "strip_ansi",
    "get_definition_from_ref",
    "get_flat_properties",
    "parse_factory_defaults",
]
