import copy
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    class LanguageAppMixinBase:
        localization: Dict[str, Any]
        ui_map: Dict[str, Any]
        app_language: str
        def _load_ui_map(self) -> Dict[str, Any]: ...
else:
    class LanguageAppMixinBase:
        pass

class LanguageAppMixin(LanguageAppMixinBase):
    def get_lang_data(self, language: str) -> dict:
        if not self.localization:
            return {}
        lang_code = None
        for code, lang_data in self.localization.items():
            if lang_data.get("language_name") == language:
                lang_code = code
                break
        if not lang_code:
            if self.localization:
                lang_code = list(self.localization.keys())[0]
            else:
                return {}
        return self.localization.get(lang_code, {})

    def apply_language(self, language: str):
        """Applies the selected language strings to the UI Map. Acts as a validator."""
        self.app_language = language
        
        # Reset to base copies from studio_ui_map to avoid polluting original config
        from desktop_ui.config.studio_ui_map import STUDIO_UI_MAP
        self.ui_map = copy.deepcopy(STUDIO_UI_MAP)

        lang_data = self.get_lang_data(language)
        if not lang_data:
            print(f"[LanguageApp] WARNING: No language data found for '{language}'!")
            lang_data = {}

        settings_translations = lang_data.get("settings", {})
        tab_translations = lang_data.get("tabs", {})
        enums_translations = lang_data.get("enums", {})
        
        new_ui_map = {}
        
        for tab_name, widgets in self.ui_map.items():
            if tab_name.startswith("__"):
                continue
                
            # Translate the tab name
            translated_tab_name = tab_translations.get(tab_name)
            if not translated_tab_name:
                print(f"\033[91m[LanguageApp] ERROR: Missing translation for Tab ID: '{tab_name}'\033[0m")
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
                    print(f"\033[91m[LanguageApp] ERROR: Missing translation for Widget ID: '{key}' in tab '{tab_name}'\033[0m")
                    info["label"] = "<Not Named>"
                    info["tooltip"] = ""
                    
                if "values" in info and isinstance(info["values"], list):
                    value_map = {}
                    for v in info["values"]:
                        value_map[v] = enums_translations.get(v, v)
                    info["value_map"] = value_map

        # Restore any dunder keys
        for k, v in self.ui_map.items():
            if k.startswith("__"):
                new_ui_map[k] = v
                
        self.ui_map = new_ui_map

        # Dynamically update the app_language dropdown options
        for tab_name, widgets in self.ui_map.items():
            if not isinstance(widgets, dict): continue
            if "app_language" in widgets:
                languages_list = []
                for l_code, l_data in self.localization.items():
                    disp_name = l_data.get("language_name", l_code.capitalize())
                    languages_list.append(disp_name)
                if languages_list:
                    widgets["app_language"]["values"] = sorted(list(set(languages_list)))
