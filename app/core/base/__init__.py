"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.base
- RESPONSIBILITY: Expose core base components.
- CALLED BY: app.core.base.manager, desktop_ui.config.loader
- CALLS TO: app.core.base.base_loader, app.core.base.io, app.core.base.parser, app.core.base.schema_loader, app.core.base.manager
- IN = OUT: Initialization module.
=============================================================================
"""
from .base_loader import BaseConfigLoader
from .io import load_yaml_file, save_yaml_file
from .schema_loader import load_backend_schema, parse_schema_output, strip_ansi
from .parser import get_definition_from_ref, get_flat_properties, parse_factory_defaults
from .manager import ConfigManager

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
    "ConfigManager",
]
