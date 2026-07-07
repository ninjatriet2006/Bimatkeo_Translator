"""
=============================================================================
[AI_ARCH_NOTE]: LANGUAGE UI MAPPER
- RESPONSIBILITY: Translates the raw UI map using localization dictionaries.
- DIRECTORY: `app/core/langs/`
- PURPOSE: Iterates through the UI definition and applies localized labels, 
  tooltips, placeholders, and enum values.
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
        Returns the translated dictionary.
        """
        lang_data = self.fallback_handler.get_lang_data(lang_id)
        if not lang_data:
            print(f"[LanguageUIMapper] WARNING: No language data found for '{lang_id}'!")
            lang_data = {}

        settings_translations = lang_data.get("settings", {})
        tab_translations = lang_data.get("tabs", {})
        enums_translations = lang_data.get("enums", {})
        
        new_ui_map = {}
        
        for tab_name, widgets in raw_ui_map.items():
            if tab_name.startswith("__"):
                continue
                
            # Translate the tab name
            translated_tab_name = tab_translations.get(tab_name)
            if not translated_tab_name:
                print(f"\\033[91m[LanguageUIMapper] ERROR: Missing translation for Tab ID: '{tab_name}'\\033[0m")
                translated_tab_name = "<Not Named Tab>"
                
            new_ui_map[translated_tab_name] = widgets
            
            # Translate settings within the tab
            for key, info in widgets.items():
                if not isinstance(info, dict):
                    continue
                    
                trans = settings_translations.get(key)
                if trans:
                    info["label"] = trans.get("label", "<Not Named>")
                    info["tooltip"] = trans.get("tooltip", "")
                    if "placeholder" in trans:
                        info["placeholder"] = trans["placeholder"]
                    if "button_text" in trans:
                        info["button_text"] = trans["button_text"]
                else:
                    print(f"\\033[91m[LanguageUIMapper] ERROR: Missing translation for Widget ID: '{key}' in tab '{tab_name}'\\033[0m")
                    info["label"] = "<Not Named>"
                    info["tooltip"] = ""
                    
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
