"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.complex_widgets
- RESPONSIBILITY: complex_widgets.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.components.widget_factory.complex_widgets.
=============================================================================
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QButtonGroup, QPushButton, QComboBox, QGridLayout
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from app.core.desktop.components.widgets_helper import SearchableComboBox
from app.core.desktop.constants import CAT_OFFLINE_MODELS, CAT_API_BASED

class ComplexWidgetFactory:
    def __init__(self, main_window):
        self.mw = main_window

    def create_segmented_button(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button_group = QButtonGroup(container)
        button_group.setExclusive(True)

        values = info.get("values", [])
        value_map = info.get("value_map", {})
        for val in values:
            display_name = value_map.get(val, val)
            button = QPushButton(str(display_name))
            button.setProperty("internal_id", val)
            button.setCheckable(True)
            if val == info.get("default"):
                button.setChecked(True)
            layout.addWidget(button)
            button_group.addButton(button)

        return container

    def set_combobox_value_by_data(self, combo_box, value):
        index = -1
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == value:
                index = i
                break
        if index != -1:
            combo_box.setCurrentIndex(index)
        else:
            combo_box.setCurrentText(str(value))

    def create_combobox(self, info: dict) -> QComboBox:
        import app.core.desktop.main_window as mw_module
        combo_box = SearchableComboBox()
        values = info.get("values", [])
        key = info.get("key")

        if key == "offline_translator":
            values = mw_module.TRANSLATOR_GROUPS.get(CAT_OFFLINE_MODELS, values)
        elif key == "ai_translator":
            values = mw_module.TRANSLATOR_GROUPS.get(CAT_API_BASED, values)

        if info.get("widget") == "optionmenu_languages":
            combo_box.addItem("--- Select ---", "none")
            for name, code in sorted(mw_module.LANGUAGES.items()):
                if code != "auto":
                    combo_box.addItem(name, code)
            self.set_combobox_value_by_data(combo_box, str(info.get("default")))
        elif info.get("widget") == "optionmenu_separators" or key in ["offline_translator", "ai_translator"]:
            if key in ["offline_translator", "ai_translator"]:
                combo_box.addItem("--- Select ---", "none")
                info["default"] = "none"
                for val in values:
                    state = self.mw.config_loader.get_model_state(val, field=key)
                    display_name = self.mw.config_loader.format_display_label(val, key)
                    if state == "NOT_SETUP":
                        display_name = f"{display_name} (Not Setup)"
                    elif state == "INCOMPLETE":
                        display_name = f"{display_name} (Incomplete)"
                    combo_box.addItem(display_name, val)
                    if state in ("NOT_SETUP", "INCOMPLETE"):
                        last_idx = combo_box.count() - 1
                        combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                lang_data = self.mw.config_loader.get_lang_data(self.mw.config_loader.app_language)
                ui_strings = lang_data.get("ui_strings", {})
                update_support_text = ui_strings.get("update_supported_langs", "📥 Update translation support list...")
                update_all_text = ui_strings.get("update_all_models", "📥 Update ALL {category} models...").replace("{category}", "software")
                combo_box.addItem(update_support_text, "update_trigger")
                combo_box.addItem(update_all_text, "update_all_software_trigger")
            else:
                for group_name, translators in mw_module.TRANSLATOR_GROUPS.items():
                    item_index = combo_box.count()
                    combo_box.addItem(group_name)
                    combo_box.model().item(item_index).setEnabled(False)  # type: ignore
                    field_name = "offline_translator" if "OFFLINE" in group_name else ("ai_translator" if "API" in group_name else None)
                    for t in translators:
                        state = self.mw.config_loader.get_model_state(t, field=field_name)
                        display_name = self.mw.config_loader.format_display_label(t, field_name)
                        if state == "NOT_SETUP":
                            display_name = f"{display_name} (Not Setup)"
                        elif state == "INCOMPLETE":
                            display_name = f"{display_name} (Incomplete)"
                        combo_box.addItem(display_name, t)
                        if state in ("NOT_SETUP", "INCOMPLETE"):
                            last_idx = combo_box.count() - 1
                            combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            self.set_combobox_value_by_data(combo_box, str(info.get("default")))
        else:
            combo_box.addItem("--- Select ---", "none")
            value_map = info.get("value_map", {})
            for val in values:
                state = self.mw.config_loader.get_model_state(val, field=key) if key != 'api_ocr' else "OK"
                display_name = value_map.get(val, self.mw.config_loader.format_display_label(val, key))
                if state == "NOT_SETUP":
                    display_name = f"{display_name} (Not Setup)"
                elif state == "INCOMPLETE":
                    display_name = f"{display_name} (Incomplete)"
                combo_box.addItem(display_name, val)
                if state in ("NOT_SETUP", "INCOMPLETE"):
                    last_idx = combo_box.count() - 1
                    combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            
            if key in ['offline_detector', 'offline_ocr', 'inpainter', 'upscaler', 'colorizer', 'renderer']:
                ui_map = getattr(self.mw.config_loader, 'ui_map', {})
                labels = ui_map.get("labels", {})
                localized_key = labels.get(key, key.replace("_", " ").title())
                
                lang_data = self.mw.config_loader.get_lang_data(self.mw.config_loader.app_language)
                ui_strings = lang_data.get("ui_strings", {})
                update_all_text_template = ui_strings.get("update_all_models", "📥 Update ALL {category} models...")
                update_all_key_text = update_all_text_template.replace("{category}", localized_key)
                combo_box.addItem(update_all_key_text, "update_all_software_trigger")
                
            self.set_combobox_value_by_data(combo_box, str(info.get("default")))

        return combo_box

    def create_grid_segmented_button(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        button_group = QButtonGroup(container)
        button_group.setExclusive(True)

        values = info.get("values", [])
        columns = info.get("options", {}).get("columns", 4)

        row, col = 0, 0
        for val in values:
            button = QPushButton(val)
            button.setCheckable(True)
            if val == info.get("default"):
                button.setChecked(True)

            layout.addWidget(button, row, col)
            button_group.addButton(button)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        return container
