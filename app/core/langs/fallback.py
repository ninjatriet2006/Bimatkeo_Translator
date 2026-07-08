"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.langs.fallback
- RESPONSIBILITY: Resolves app_language ID and provides robust fallback logic.
- CALLED BY: app.core.langs.manager
- CALLS TO: None
- IN = OUT: Evaluates dictionaries to return valid language strings.
=============================================================================
"""

from typing import Dict, Any

class LanguageFallback:
    def __init__(self, localization: Dict[str, Any]):
        self.localization = localization

    def get_lang_data(self, lang_id: str) -> dict:
        """Returns the localization dictionary for a specific lang_id in O(1) time."""
        if not self.localization:
            return {}
        
        lang_data = self.localization.get(lang_id)
        if not lang_data:
            fallback_id = list(self.localization.keys())[0]
            return self.localization.get(fallback_id, {})
            
        return lang_data

    def resolve_app_language(self, oldsession_config: dict) -> str:
        """
        Resolves the actual app_language to use, migrating legacy string names (e.g., 'English') 
        to their proper lang_id format securely.
        Modifies oldsession_config in place to reflect the migrated id.
        """
        fallback_id = list(self.localization.keys())[0] if self.localization else "en"
        old_lang = oldsession_config.get("app_language", fallback_id)
        migrated = False
        
        for lang_id, data in self.localization.items():
            if data.get("language_name") == old_lang:
                oldsession_config["app_language"] = lang_id
                migrated = True
                return lang_id
                
        if not migrated:
            if old_lang not in self.localization:
                oldsession_config["app_language"] = fallback_id
                return fallback_id
            else:
                return old_lang
                
        return fallback_id
