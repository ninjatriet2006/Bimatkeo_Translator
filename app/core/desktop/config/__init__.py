"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.config.__init__
- RESPONSIBILITY: __init__.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.config.__init__.
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
