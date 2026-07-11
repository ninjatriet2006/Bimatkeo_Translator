"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.langs.ui_mapper
- RESPONSIBILITY: Translates the raw UI map using localization dictionaries.
- CALLED BY: app.core.langs.manager
- CALLS TO: None
- IN = OUT: Injects translated strings into a nested dictionary structure.
=============================================================================
"""

from typing import Dict, Any

class LanguageUIMapper:
    def __init__(self, localization: Dict[str, Any], fallback_handler):
        self.localization = localization
        self.fallback_handler = fallback_handler

    def apply_language_to_ui_map(self, raw_ui_map: dict, lang_id: str) -> dict:
        """
        Translates a raw studio UI Map utilizing the selected localization data.
        Returns the translated dictionary. Note: Now uses ID Linking for labels and tabs,
        so it only maps enums and dynamic dropdowns here.
        """
        lang_data = self.fallback_handler.get_lang_data(lang_id)
        if not lang_data:
            print(f"[LanguageUIMapper] WARNING: No language data found for '{lang_id}'!")
            lang_data = {}

        enums_translations = lang_data.get("enums", {})
        
        new_ui_map = {}
        
        for tab_name, widgets in raw_ui_map.items():
            if tab_name.startswith("__"):
                continue
                
            # KEEP the original tab name as key for ID linking!
            new_ui_map[tab_name] = widgets
            
            # Translate settings within the tab (Only Enums & Value Maps)
            for key, info in widgets.items():
                if not isinstance(info, dict):
                    continue
                    
                if "values" in info and isinstance(info["values"], list):
                    value_map = {}
                    for v in info["values"]:
                        value_map[v] = enums_translations.get(v, v)
                    info["value_map"] = value_map

        # Restore any dunder keys
        for k, v in raw_ui_map.items():
            if k.startswith("__"):
                new_ui_map[k] = v

        # Dynamically inject the app_language dropdown options
        for tab_name, widgets in new_ui_map.items():
            if not isinstance(widgets, dict): continue
            if "app_language" in widgets:
                widgets["app_language"]["values"] = sorted(list(self.localization.keys()))
                widgets["app_language"]["value_map"] = {
                    k: v.get("language_name", k.capitalize()) for k, v in self.localization.items()
                }

        return new_ui_map
