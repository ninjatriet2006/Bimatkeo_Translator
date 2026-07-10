import os
import string
from PySide6.QtCore import QObject

class ThemeManager(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        self.available_themes = {}
        self.theme_colors = {}
        
    def load_themes(self, theme_combobox, project_base_dir):
        """Scans the themes directory and populates the theme combobox."""
        self.available_themes.clear()
        themes_dir = os.path.join(project_base_dir, "themes")
        self.available_themes["Default Qt"] = {"name": "Default Qt", "style": {}}

        if not os.path.isdir(themes_dir):
            theme_combobox.addItems(sorted(self.available_themes.keys()))
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
                        self.available_themes[theme_name] = theme_data
                except Exception as e:
                    print(f"Warning: Could not load theme file {filename}. Error: {e}")

        theme_combobox.addItems(sorted(self.available_themes.keys()))

    def apply_theme(self, theme_name: str, project_base_dir: str, font_size_text: str = "100%", get_arrow_func=None):
        """Applies the selected theme's stylesheet to the entire application."""
        percentage = int(font_size_text.split('%')[0])
        base_font_size = 10
        font_size = f"{base_font_size * (percentage / 100.0)}pt"

        if theme_name == "Default Qt":
            qss_path = os.path.join(project_base_dir, "themes", "default.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss_content = f.read()
                template = string.Template(qss_content)
                minimal_style = template.safe_substitute(font_size=font_size)
                self.main_window.setStyleSheet(minimal_style)
            else:
                self.main_window.setStyleSheet(f"QWidget {{ font-size: {font_size}; }}")
            self.theme_colors = {}
            if hasattr(self.main_window, 'app_logger'):
                self.main_window.app_logger.log("INFO", "Reverted to default Qt theme.")
            return

        theme_data = self.available_themes.get(theme_name)
        if not theme_data or "style" not in theme_data:
            return

        colors = theme_data["style"].get("colors", {})
        self.theme_colors = colors
        
        arrow_icon_path = ""
        if get_arrow_func:
            arrow_icon_path = get_arrow_func(colors.get("text_main", "#dce4ee"), theme_name)
        
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

        qss_path = os.path.join(project_base_dir, "themes", "template.qss")
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                qss_content = f.read()
            template = string.Template(qss_content)
            style_sheet = template.safe_substitute(mapping)
            self.main_window.setStyleSheet(style_sheet)
        
        if hasattr(self.main_window, 'app_logger'):
            self.main_window.app_logger.log("INFO", f"Theme '{theme_name}' applied successfully.")
