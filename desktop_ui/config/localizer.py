import copy

class LocalizerMixin:
    def localize_ui_map(self, language: str):
        """Localizes the ui_map and tasks_config based on the selected language."""
        self.app_language = language
        
        # Reset to base copies from studio_config/files to avoid polluting original config & double localization
        self.ui_map = copy.deepcopy(self._load_ui_map())
        self.tasks_config = copy.deepcopy(self._load_tasks_config())

        if not self.localization:
            return
 
        # Find lang_code dynamically by matching display name
        lang_code = None
        for code, lang_data in self.localization.items():
            if lang_data.get("language_name") == language:
                lang_code = code
                break
        if not lang_code:
            lang_code = "vi" if language == "Tiếng Việt" else "en"
 
        lang_data = self.localization.get(lang_code, {})
        if not lang_data:
            return

        # 1. Localize settings
        settings_translations = lang_data.get("settings", {})
        for key, info in self.ui_map.items():
            if key.startswith("__"):
                continue
            trans = settings_translations.get(key)
            if trans:
                if "label" in trans:
                    info["label"] = trans["label"]
                if "tooltip" in trans:
                    info["tooltip"] = trans["tooltip"]

        # 2. Localize tab names in ui_map keys or tab order
        tab_translations = lang_data.get("tabs", {})
        for key, info in self.ui_map.items():
            if key.startswith("__"):
                continue
            group = info.get("group")
            if group in tab_translations:
                info["group"] = tab_translations[group]

        # Translate __tab_order__ list
        if "__tab_order__" in self.ui_map:
            translated_order = []
            for tab in self.ui_map["__tab_order__"]:
                translated_order.append(tab_translations.get(tab, tab))
            self.ui_map["__tab_order__"] = translated_order

        # 3. Localize tasks_config
        task_translations = lang_data.get("tasks", {})
        for task_key, task_info in self.tasks_config.items():
            trans = task_translations.get(task_key)
            if trans:
                if "label" in trans:
                    task_info["label"] = trans["label"]
                if "description" in trans:
                    task_info["description"] = trans["description"]

        # Dynamically update the app_language dropdown options in the localized ui_map
        if "app_language" in self.ui_map:
            languages_list = []
            for l_code, l_data in self.localization.items():
                disp_name = l_data.get("language_name", l_code.capitalize())
                languages_list.append(disp_name)
            if languages_list:
                self.ui_map["app_language"]["values"] = sorted(list(set(languages_list)))
