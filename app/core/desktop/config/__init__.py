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
