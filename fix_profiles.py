import re

file_path = "/home/bimatkeo/Documents/Translator/Bimatkeo_Translator/desktop_ui/mainwindow/handlers.py"
with open(file_path, "r", encoding="utf-8") as f:
    content = f.read()

new_methods = """
    def _get_preset_profiles_file_path(self) -> str:
        import os
        base_dir = os.path.join(self.project_base_dir, '.config', 'configs')
        os.makedirs(base_dir, exist_ok=True)
        return os.path.join(base_dir, 'profiles.yaml')

    def _load_preset_profiles(self) -> dict:
        import os
        import yaml
        path = self._get_preset_profiles_file_path()
        if os.path.exists(path):
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"[ERROR] Failed to load preset profiles: {e}")
        return {}

    def _save_preset_profiles(self, profiles: dict):
        import yaml
        path = self._get_preset_profiles_file_path()
        try:
            with open(path, 'w', encoding='utf-8') as f:
                yaml.dump(profiles, f, allow_unicode=True, default_flow_style=False, sort_keys=False)
        except Exception as e:
            print(f"[ERROR] Failed to save preset profiles: {e}")

    def _refresh_profile_list(self):
        \"\"\"Reloads the list of profiles from the unified config and updates the combobox.\"\"\"
        try:
            profiles = sorted(list(self._load_preset_profiles().keys()))
            self.profile_combobox.clear()
            if profiles:
                self.profile_combobox.addItems(profiles)
            else:
                self.profile_combobox.addItem("No profiles found")
        except Exception as e:
            print(f"[ERROR] Failed to refresh profiles: {e}")

    def _save_profile(self):
        \"\"\"Saves the current settings dictionary as a profile in the unified config.\"\"\"
        name = self.profile_name_entry.text().strip()
        if not name:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.warning(self, "Warning", "Please enter a profile name.")
            return

        profiles = self._load_preset_profiles()
        if name in profiles:
            from PySide6.QtWidgets import QMessageBox
            reply = QMessageBox.question(self, "Confirm Overwrite", f"Profile '{name}' already exists. Overwrite it?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.No:
                return

        try:
            import copy
            profiles[name] = copy.deepcopy(self.current_settings)
            self._save_preset_profiles(profiles)
            self._refresh_profile_list()
            self.profile_combobox.setCurrentText(name)
            print(f"Profile '{name}' saved successfully.")
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to save profile: {e}")

    def _load_profile(self):
        \"\"\"Loads a profile from the unified config and applies its settings, ensuring the UI remains enabled.\"\"\"
        name = self.profile_combobox.currentText()
        if not name or name == "No profiles found":
            return

        profiles = self._load_preset_profiles()
        if name not in profiles:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Profile not found in config: {name}")
            self._refresh_profile_list()
            return

        try:
            import copy
            loaded_settings = copy.deepcopy(profiles[name])

            job_index = self._get_selected_job_index()
            if job_index is not None:
                self.job_queue[job_index]['settings'].update(loaded_settings)
            else:
                self.current_settings.update(loaded_settings)

            self._populate_settings_panel()

            if 'translator_chain' in loaded_settings:
                self._rebuild_chain_from_string(loaded_settings['translator_chain'])

            self._update_chain_ui_state()
            self._set_settings_panel_enabled(job_index is not None)
            self.log("SUCCESS", f"Profile '{name}' loaded and applied.")
            print(f"Profile '{name}' loaded successfully.")

        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            error_message = f"An unexpected error occurred while loading profile '{name}'.\\n\\nDetails: {e}"
            print(f"[ERROR] {error_message}")
            QMessageBox.critical(self, "Profile Load Error", error_message)
        self._set_settings_panel_enabled(True)

    def _delete_profile(self):
        \"\"\"Deletes the selected profile from the unified config.\"\"\"
        name = self.profile_combobox.currentText()
        if not name or name == "No profiles found":
            return

        from PySide6.QtWidgets import QMessageBox
        reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete profile '{name}'?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.No:
            return

        profiles = self._load_preset_profiles()
        try:
            if name in profiles:
                del profiles[name]
                self._save_preset_profiles(profiles)
                print(f"Profile '{name}' deleted.")
                self._refresh_profile_list()
        except Exception as e:
            from PySide6.QtWidgets import QMessageBox
            QMessageBox.critical(self, "Error", f"Failed to delete profile: {e}")
            print(f"[ERROR] Failed to delete profile '{name}': {e}")"""

start_idx = content.find("    def _refresh_profile_list(self):")
end_idx = content.find("    def _on_font_scale_changed(self, text: str):")

if start_idx != -1 and end_idx != -1:
    new_content = content[:start_idx] + new_methods + "\n\n" + content[end_idx:]
    with open(file_path, "w", encoding="utf-8") as f:
        f.write(new_content)
    print("Successfully replaced profiles methods in handlers.py")
else:
    print("Could not find start or end index for replacement")

