"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.langs.manager
- RESPONSIBILITY: Centralized management of application localization logic.
- CALLED BY: desktop_ui.config.loader
- CALLS TO: app.core.langs.loader, app.core.langs.fallback, app.core.langs.ui_mapper
- IN = OUT: Coordinator module, delegates concrete actions to submodules.
=============================================================================
"""

from typing import Dict, Any
from .loader import LanguageLoader
from .fallback import LanguageFallback
from .ui_mapper import LanguageUIMapper
from .verify import LanguageVerifier
import logging

logger = logging.getLogger(__name__)

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
        self.verifier = LanguageVerifier(self.localization)

    def run_verification(self, raw_ui_map: dict):
        self.verifier.run_verification(raw_ui_map)

    def get_lang_data(self, lang_id: str) -> dict:
        return self.fallback.get_lang_data(lang_id)

    def resolve_app_language(self, oldsession_config: dict) -> str:
        return self.fallback.resolve_app_language(oldsession_config)

    def apply_language_to_ui_map(self, raw_ui_map: dict, lang_id: str) -> dict:
        return self.ui_mapper.apply_language_to_ui_map(raw_ui_map, lang_id)

    def get_string(self, lang_id: str, string_id: str, **kwargs) -> str:
        """
        Retrieves a translated string by its ID. Supports parameter formatting via **kwargs.
        """
        lang_data = self.get_lang_data(lang_id)
        if not lang_data:
            return string_id

        messages = lang_data.get("messages", {})
        ui_strings = lang_data.get("ui_strings", {})

        translated_text = messages.get(string_id)
        if translated_text is None:
            translated_text = ui_strings.get(string_id)

        if translated_text is None:
            logger.warning(f"[LanguageManager] Missing translation for string ID '{string_id}' in language '{lang_id}'")
            return string_id

        if kwargs:
            try:
                translated_text = translated_text.format(**kwargs)
            except Exception as e:
                logger.error(f"[LanguageManager] Formatting error for ID '{string_id}': {e}")

        return translated_text

    def get_ui_string(self, lang_id: str, category: str, string_id: str, sub_key: str = None) -> str:
        """
        Retrieves a translated UI string (tabs, settings, enums).
        category: 'tabs', 'settings', 'enums'
        sub_key: for 'settings', e.g. 'label', 'tooltip', 'placeholder'
        """
        lang_data = self.get_lang_data(lang_id)
        if not lang_data:
            logger.warning(f"[LanguageManager] Language data not found for '{lang_id}'")
            return string_id

        cat_data = lang_data.get(category, {})
        trans = cat_data.get(string_id)

        if trans is None:
            logger.warning(f"[LanguageManager] Missing UI string for '{category}' -> '{string_id}' in language '{lang_id}'")
            return string_id
            
        if sub_key and isinstance(trans, dict):
            sub_trans = trans.get(sub_key)
            if sub_trans is None:
                logger.warning(f"[LanguageManager] Missing sub_key '{sub_key}' for '{category}' -> '{string_id}' in language '{lang_id}'")
                return string_id
            return sub_trans
        elif isinstance(trans, str):
            return trans
            
        return string_id
