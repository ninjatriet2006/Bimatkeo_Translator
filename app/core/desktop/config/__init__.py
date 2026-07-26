"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.config.__init__
- RESPONSIBILITY: Configuration loader entry point delegating core config management to app.core.base.manager.ConfigManager via composition.
- CALLED BY: app.core.desktop.main_window, app.core.desktop.logic.*
- CALLS TO: app.core.base.manager.ConfigManager, app.core.desktop.config.base_loader
- IN = OUT: Instantiates ConfigManager via composition and builds complete desktop configuration.
=============================================================================
"""
# type: ignore
# ===============================================================
# ConfigLoader - Entry Point for Configuration
#
# Author: User & Gemini Collaboration
# ===============================================================

from .base_loader import ConfigLoaderBase
from .schema import SchemaMixin
from app.core.base.config_repair import RepairMixin
from .capabilities import CapabilitiesMixin
from .registry import RegistryMixin

class ConfigLoader(ConfigLoaderBase, RegistryMixin, SchemaMixin, RepairMixin, CapabilitiesMixin):
    def __init__(self, project_base_dir):
        super().__init__(project_base_dir)
