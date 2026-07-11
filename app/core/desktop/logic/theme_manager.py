"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.theme_manager
- RESPONSIBILITY: Apply application UI themes (Dark/Light).
- CALLED BY: app.core.desktop.logic.core_handlers.themes
- CALLS TO: PySide6.QtWidgets, PySide6.QtGui
- IN = OUT: Reads QSS files from config and applies them to QApplication.
=============================================================================
"""
import os
import string

class ThemeManager:
    def __init__(self, main_window):
        self.mw = main_window

    def load_themes(self):
        self.mw.available_themes.clear()
        themes_dir = os.path.join(self.mw.project_base_dir, "themes")
        self.mw.available_themes["Default Qt"] = {"name": "Default Qt", "style": {}}

        if not os.path.isdir(themes_dir):
            self.mw.theme_combobox.addItems(sorted(self.mw.available_themes.keys()))
            return

        from ruamel.yaml import YAML
        yaml = YAML()
        yaml.preserve_quotes = True
        yaml.default_flow_style = False
        for filename in os.listdir(themes_dir):
            if filename.endswith(".yaml"):
                try:
                    filepath = os.path.join(themes_dir, filename)
                    with open(filepath, 'r', encoding='utf-8') as f:
                        theme_data = yaml.load(f) or {}
                        theme_name = theme_data.get("name", filename)
                        self.mw.available_themes[theme_name] = theme_data
                except Exception as e:
                    print(f"Warning: Could not load theme file {filename}. Error: {e}")

        self.mw.theme_combobox.addItems(sorted(self.mw.available_themes.keys()))

    def apply_theme(self, theme_name: str):
        if hasattr(self.mw, 'font_scale_combobox'):
            font_size_text = self.mw.font_scale_combobox.currentText()
        else:
            font_size_text = "100%"
        percentage = int(font_size_text.split('%')[0])
        base_font_size = 10
        font_size = f"{base_font_size * (percentage / 100.0)}pt"

        if theme_name == "Default Qt":
            qss_path = os.path.join(self.mw.project_base_dir, "themes", "default.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss_content = f.read()
                template = string.Template(qss_content)
                minimal_style = template.safe_substitute(font_size=font_size)
                self.mw.setStyleSheet(minimal_style)
            else:
                self.mw.setStyleSheet(f"QWidget {{ font-size: {font_size}; }}")
            self.mw.theme_colors = {}
            self.mw.log("INFO", "msg_revert_theme")
            return

        theme_data = self.mw.available_themes.get(theme_name)
        if not theme_data or "style" not in theme_data:
            return

        colors = theme_data["style"].get("colors", {})
        self.mw.theme_colors = colors
        
        arrow_icon_path = self.mw._get_themed_arrow_icon_path(colors.get("text_main", "#dce4ee"), theme_name)
        
        mapping = {
            "font_size": font_size,
            "background_main": colors.get("background_main", "#2d2d2d"),
            "background_frame": colors.get("background_frame", "#2d2d2d"),
            "primary_button": colors.get("primary_button", "#3a7ebf"),
            "primary_button_hover": colors.get("primary_button_hover", "#56a9e8"),
            "slider_groove": colors.get("slider_groove", "#242424"),
            "slider_handle": colors.get("slider_handle", "#3a7ebf"),
            "text_main": colors.get("text_main", "#dce4ee"),
            "border": colors.get("border", "#555555"),
            "accent": colors.get("accent", "#4a9fcf"),
            "arrow_icon_path": arrow_icon_path
        }

        qss_path = os.path.join(self.mw.project_base_dir, "themes", "template.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                qss_content = f.read()
            template = string.Template(qss_content)
            style_sheet = template.safe_substitute(mapping)
            self.mw.setStyleSheet(style_sheet)
        
        self.mw.log("INFO", f"msg_theme_applied|theme_name={theme_name}")
