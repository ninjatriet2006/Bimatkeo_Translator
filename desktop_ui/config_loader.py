# type: ignore
# ===============================================================
# ConfigLoader - Entry Point for Configuration
#
# Author: User & Gemini Collaboration
# ===============================================================

from .config.loader import ConfigLoaderBase
from .config.schema import SchemaMixin
from .config.localizer import LocalizerMixin
from .config.repair import RepairMixin
from .config.capabilities import CapabilitiesMixin
from .config.registry import RegistryMixin

class ConfigLoader(ConfigLoaderBase, RegistryMixin, SchemaMixin, LocalizerMixin, RepairMixin, CapabilitiesMixin):
    def __init__(self, project_base_dir):
        super().__init__(project_base_dir)
