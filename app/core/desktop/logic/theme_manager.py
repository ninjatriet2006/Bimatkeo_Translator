"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.theme_manager
- RESPONSIBILITY: Decoupled theme manager for loading and applying application UI themes.
- CALLED BY: app.core.desktop.logic.core_handlers.themes, app.core.desktop.main_window
- CALLS TO: PySide6.QtWidgets, PySide6.QtGui
- IN = OUT: Primitive parameter project_base_dir into __init__, emits PySide6 Signals.
=============================================================================
"""
import os
import string
from PySide6.QtCore import QObject, Signal
from app.core.desktop.components.ui_utils import natural_sort_key

class ThemeManager(QObject):
    theme_applied = Signal(str, dict, str)  # (theme_name, theme_colors, stylesheet)
    log_requested = Signal(str, str)        # (level, message)

    def __init__(self, project_base_dir: str = "."):
        super().__init__()
        self.project_base_dir = project_base_dir

    def get_themed_arrow_icon_path(self, color_hex: str, theme_name: str, main_window=None) -> str:
        if main_window and hasattr(main_window, '_get_themed_arrow_icon_path'):
            return main_window._get_themed_arrow_icon_path(color_hex, theme_name)
        return ""

    def load_themes(self, available_themes_dict: dict = None, theme_combobox=None, main_window=None) -> dict:
        mw = main_window
        target_dict = available_themes_dict if available_themes_dict is not None else getattr(mw, 'available_themes', {})
        target_dict.clear()
        target_dict["Default Qt"] = {"name": "Default Qt", "style": {}}

        themes_dir = os.path.join(self.project_base_dir, "themes")
        combo = theme_combobox or getattr(mw, 'theme_combobox', None)

        if not os.path.isdir(themes_dir):
            if combo:
                combo.addItems(sorted(target_dict.keys(), key=natural_sort_key))
            return target_dict

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
                        target_dict[theme_name] = theme_data
                except Exception as e:
                    print(f"Warning: Could not load theme file {filename}. Error: {e}")

        if combo:
            combo.addItems(sorted(target_dict.keys(), key=natural_sort_key))

        return target_dict

    def apply_theme(self, theme_name: str, font_scale_combobox=None, available_themes: dict = None, main_window=None) -> tuple[dict, str]:
        mw = main_window
        font_combo = font_scale_combobox or getattr(mw, 'font_scale_combobox', None)
        font_size_text = font_combo.currentText() if font_combo else "100%"
        
        try:
            percentage = int(font_size_text.split('%')[0])
        except ValueError:
            percentage = 100

        base_font_size = 10
        font_size = f"{base_font_size * (percentage / 100.0)}pt"

        if theme_name == "Default Qt":
            qss_path = os.path.join(self.project_base_dir, "themes", "default.qss")
            if os.path.exists(qss_path):
                with open(qss_path, "r", encoding="utf-8") as f:
                    qss_content = f.read()
                template = string.Template(qss_content)
                minimal_style = template.safe_substitute(font_size=font_size)
                if mw:
                    mw.setStyleSheet(minimal_style)
                    mw.theme_colors = {}
                    if hasattr(mw, 'log'):
                        mw.log("SUCCESS", "Reverted to Default Qt Theme.")
                self.theme_applied.emit("Default Qt", {}, minimal_style)
                return {}, minimal_style
            else:
                fallback_style = f"QWidget {{ font-size: {font_size}; }}"
                if mw:
                    mw.setStyleSheet(fallback_style)
                    mw.theme_colors = {}
                self.theme_applied.emit("Default Qt", {}, fallback_style)
                return {}, fallback_style

        themes_dict = available_themes if available_themes is not None else getattr(mw, 'available_themes', {})
        theme_data = themes_dict.get(theme_name)
        if not theme_data or "style" not in theme_data:
            return {}, ""

        colors = theme_data["style"].get("colors", {})
        if mw:
            mw.theme_colors = colors

        arrow_icon_path = self.get_themed_arrow_icon_path(colors.get("text_main", "#dce4ee"), theme_name, main_window=mw)

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

        qss_path = os.path.join(self.project_base_dir, "themes", "template.qss")
        style_sheet = ""
        if os.path.exists(qss_path):
            with open(qss_path, "r", encoding="utf-8") as f:
                qss_content = f.read()
            template = string.Template(qss_content)
            style_sheet = template.safe_substitute(mapping)
            if mw:
                mw.setStyleSheet(style_sheet)
                if hasattr(mw, 'log'):
                    mw.log("SUCCESS", f"Theme '{theme_name}' applied successfully.")

        self.theme_applied.emit(theme_name, colors, style_sheet)
        return colors, style_sheet

