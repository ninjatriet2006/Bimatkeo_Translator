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

class ConfigLoader(ConfigLoaderBase, SchemaMixin, LocalizerMixin, RepairMixin, CapabilitiesMixin):
    def __init__(self, project_base_dir):
        super().__init__(project_base_dir)
