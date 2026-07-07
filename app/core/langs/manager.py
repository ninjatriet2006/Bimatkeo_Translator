"""
=============================================================================
[AI_ARCH_NOTE]: LANGUAGE MANAGER
- RESPONSIBILITY: Centralized management of application localization logic.
- DIRECTORY: `app/core/langs/`
- PURPOSE: Controller facade that coordinates loader, fallback, and ui_mapper.
- DECOUPLES: Removes logic from Manager itself, delegating to specialized modules.
=============================================================================
"""

from typing import Dict, Any
from .loader import LanguageLoader
from .fallback import LanguageFallback
from .ui_mapper import LanguageUIMapper

class LanguageManager:
    """
    Central facade for all localization operations.
    Delegates to loader, fallback, and ui_mapper.
    """
    def __init__(self, project_base_dir: str):
        self.project_base_dir = project_base_dir
        
        # Instantiate sub-components
        self.loader = LanguageLoader(self.project_base_dir)
        self.localization = self.loader.load_localization_files()
        
        self.fallback = LanguageFallback(self.localization)
        self.ui_mapper = LanguageUIMapper(self.localization, self.fallback)

    def get_lang_data(self, lang_id: str) -> dict:
        return self.fallback.get_lang_data(lang_id)

    def resolve_app_language(self, oldsession_config: dict) -> str:
        return self.fallback.resolve_app_language(oldsession_config)

    def apply_language_to_ui_map(self, raw_ui_map: dict, lang_id: str) -> dict:
        return self.ui_mapper.apply_language_to_ui_map(raw_ui_map, lang_id)
