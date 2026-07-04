import copy
from typing import TYPE_CHECKING, Dict, Any

if TYPE_CHECKING:
    class LocalizerMixinBase:
        localization: Dict[str, Any]
        ui_map: Dict[str, Any]
        app_language: str
        def _load_ui_map(self) -> Dict[str, Any]: ...
else:
    class LocalizerMixinBase:
        pass

class LocalizerMixin(LocalizerMixinBase):
    def get_lang_data(self, language: str) -> dict:
        if not self.localization:
            return {}
        lang_code = None
        for code, lang_data in self.localization.items():
            if lang_data.get("language_name") == language:
                lang_code = code
                break
        if not lang_code:
            lang_code = "vi" if language == "Tiếng Việt" else "en"
        return self.localization.get(lang_code, {})

    def localize_ui_map(self, language: str):
        """Localizes the ui_map based on the selected language."""
        self.app_language = language
        
        # Reset to base copies from studio_config/files to avoid polluting original config & double localization
        self.ui_map = copy.deepcopy(self._load_ui_map())


        lang_data = self.get_lang_data(language)
        if not lang_data:
            return

        # 1. Localize settings
        settings_translations = lang_data.get("settings", {})
        
        # We must build a new dict to rename keys (translate tab names)
        new_ui_map = {}
        tab_translations = lang_data.get("tabs", {})
        
        for tab_name, widgets in self.ui_map.items():
            if tab_name.startswith("__"):
                continue
                
            # Translate the tab name
            translated_tab_name = tab_translations.get(tab_name, tab_name)
            new_ui_map[translated_tab_name] = widgets
            
            # Translate settings within the tab
            for key, info in widgets.items():
                trans = settings_translations.get(key)
                if trans:
                    if "label" in trans:
                        info["label"] = trans["label"]
                    if "tooltip" in trans:
                        info["tooltip"] = trans["tooltip"]

        # Restore any dunder keys
        for k, v in self.ui_map.items():
            if k.startswith("__"):
                new_ui_map[k] = v
                
        self.ui_map = new_ui_map



        # Dynamically update the app_language dropdown options in the localized ui_map
        for tab_name, widgets in self.ui_map.items():
            if not isinstance(widgets, dict): continue
            if "app_language" in widgets:
                languages_list = []
                for l_code, l_data in self.localization.items():
                    disp_name = l_data.get("language_name", l_code.capitalize())
                    languages_list.append(disp_name)
                if languages_list:
                    widgets["app_language"]["values"] = sorted(list(set(languages_list)))
