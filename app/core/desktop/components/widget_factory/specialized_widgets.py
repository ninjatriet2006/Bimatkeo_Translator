"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.specialized_widgets
- RESPONSIBILITY: specialized_widgets.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.components.widget_factory.specialized_widgets.
=============================================================================
"""
import os
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QFrame,
    QListWidget, QListWidgetItem, QMessageBox, QComboBox
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from app.core.desktop.components.widgets_helper import DynamicHeightListWidget, NoScrollComboBox, SearchableComboBox
from app.core.desktop.components.ui_utils import natural_sort_key
from app.core.desktop.constants import INSTALL_NEW_FONT, UPDATE_ALL_FONTS

class SpecializedWidgetFactory:
    def __init__(self, main_window):
        self.mw = main_window

    def create_api_profile_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        service = info.get("service", "Translator")
        
        combo = SearchableComboBox()
        profiles = self.mw._load_api_profiles()
        
        filtered_profiles = []
        from app.core.shared_registry import MultimodalFactory
        
        for name, p in profiles.items():
            if p.get("type", p.get("group", "Standalone")) != "Standalone":
                continue
                
            # Trạch xuất provider để kiểm tra năng lực
            provider = p.get("provider", "")
            
            # Nếu profile cũ còn giữ key 'service', vẫn tôn trọng nó
            if "service" in p:
                if p["service"] == service:
                    filtered_profiles.append(name)
            else:
                # Cơ chế mới: Kiểm tra Provider có support service này không
                supported = False
                multimodal_class = MultimodalFactory.get_class(provider)
                if multimodal_class and hasattr(multimodal_class, "get_supported_services"):
                    if service in multimodal_class.get_supported_services():
                        supported = True
                else:
                    # Fallback cho các provider cũ chưa nâng cấp
                    if service == "Translator":
                        supported = True # Đa số là Translator
                        
                if supported:
                    filtered_profiles.append(name)

        combo.addItem("--- Select ---")
        combo.addItems(sorted(filtered_profiles, key=natural_sort_key))
        
        default_val = self.mw.current_settings.get(info['key'], info.get("default", ""))
        combo.setCurrentText(str(default_val) if default_val else "--- Select ---")
            
        layout.addWidget(combo, stretch=1)
        
        save_btn = QPushButton("+")
        save_btn.setFixedWidth(30)
        save_btn.setToolTip("Save this profile to local config")
        save_btn.clicked.connect(lambda _, s=service: self.mw._save_api_profile_generic(s))
        layout.addWidget(save_btn)
        
        del_btn = QPushButton("-")
        del_btn.setFixedWidth(30)
        del_btn.setToolTip("Delete this profile from local config")
        del_btn.clicked.connect(lambda _, s=service: self.mw._delete_api_profile_generic(s))
        layout.addWidget(del_btn)
        
        self.mw.widget_references[info['key']] = combo
        return container

    def create_pool_profile_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        service = info.get("service", "Translator")
        
        combo = SearchableComboBox()
        pools = self.mw._load_pool_profiles(service)
        filtered_pools = list(pools.keys())
            
        combo.addItem("--- Select ---")
        combo.addItems(sorted(filtered_pools, key=natural_sort_key))
        
        default_val = self.mw.current_settings.get(info['key'], info.get("default", ""))
        combo.setCurrentText(str(default_val) if default_val else "--- Select ---")
            
        layout.addWidget(combo, stretch=1)
        
        manage_text = self.mw.get_string("ui_manage_pools") if self.mw.get_string("ui_manage_pools") != "ui_manage_pools" else "⚙️ Manage Pools"
        manage_btn = QPushButton(manage_text)
        manage_btn.setProperty("lang_id", "ui_manage_pools")
        manage_btn.setProperty("lang_type", "ui")
        manage_btn.setToolTip("Open Manage Pools Dialog")
        manage_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        manage_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                color: #0078D7;
                border: 1px solid #0078D7;
                border-radius: 4px;
                padding: 4px 12px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: rgba(0, 120, 215, 0.1);
            }
            QPushButton:pressed {
                background-color: rgba(0, 120, 215, 0.2);
            }
        """)
        manage_btn.clicked.connect(lambda _, s=service: self.mw._open_manage_pools_dialog(s))
        layout.addWidget(manage_btn)
        
        self.mw.widget_references[info['key']] = combo
        return container

    def create_ai_model_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        combo = SearchableComboBox()
        combo.setEditable(True)
        
        combo.addItem("Auto")
        
        default_val = info.get("default", "")
        if default_val and default_val != "Auto":
            combo.addItem(str(default_val))
            combo.setCurrentText(str(default_val))
        else:
            combo.setCurrentText("Auto")
            
        layout.addWidget(combo, stretch=1)
        
        btn_fetch = QPushButton("Fetch")
        btn_fetch.setFixedWidth(50)
        btn_fetch.setCursor(Qt.CursorShape.PointingHandCursor)
        
        btn_test = QPushButton("Test")
        btn_test.setFixedWidth(50)
        btn_test.setCursor(Qt.CursorShape.PointingHandCursor)

        if info.get('key') == 'ocr_api_model':
            api_name_field = 'ocr_api_name'
            endpoint_field = 'ocr_api_endpoint'
            key_field = 'ocr_api_key'
        else:
            api_name_field = 'api_name'
            endpoint_field = 'ai_endpoint'
            key_field = 'ai_key'

        def _get_api_name():
            api_name = ""
            if api_name_field in self.mw.setting_widgets:
                api_name = self.mw.setting_widgets[api_name_field].currentData()
                if not api_name:
                    api_name = self.mw.setting_widgets[api_name_field].currentText()
            return api_name

        def _get_endpoint():
            return self.mw.setting_widgets[endpoint_field].text() if endpoint_field in self.mw.setting_widgets else ""

        def _get_key():
            return self.mw.setting_widgets[key_field].text() if key_field in self.mw.setting_widgets else ""

        def on_fetch():
            from app.core.desktop.components.standalone.translator_widget import TranslatorStandaloneWidget
            if not hasattr(self.mw, '_temp_standalone_widget'):
                self.mw._temp_standalone_widget = TranslatorStandaloneWidget()
            
            standalone = self.mw._temp_standalone_widget
            api_name = _get_api_name()
            
            standalone.combo_model.clear()
            if api_name:
                standalone.combo_model.addItem(api_name, api_name)
                standalone.combo_model.setCurrentIndex(0)
                
            standalone.txt_endpoint.setText(_get_endpoint())
            standalone.txt_key.setText(_get_key())
            
            def handle_fetch_success(models):
                if models:
                    current_text = combo.currentText()
                    combo.clear()
                    combo.addItem("Auto")
                    from app.core.desktop.components.ui_utils import natural_sort_key
                    combo.addItems(sorted(models, key=natural_sort_key))
                    if current_text and (current_text in models or current_text == "Auto"):
                        combo.setCurrentText(current_text)
                    else:
                        combo.setCurrentText("Auto")
            
            try:
                standalone.fetch_success_signal.disconnect()
                standalone.fetch_fail_signal.disconnect()
            except Exception:
                pass
                
            standalone.fetch_success_signal.connect(standalone._on_fetch_success)
            standalone.fetch_fail_signal.connect(standalone._on_fetch_fail)
            standalone.fetch_success_signal.connect(handle_fetch_success)
            
            standalone._on_fetch_models()
            
        def on_test():
            from app.core.desktop.components.standalone.translator_widget import TranslatorStandaloneWidget
            if not hasattr(self.mw, '_temp_standalone_widget'):
                self.mw._temp_standalone_widget = TranslatorStandaloneWidget()
            
            standalone = self.mw._temp_standalone_widget
            api_name = _get_api_name()
            
            standalone.combo_model.clear()
            if api_name:
                standalone.combo_model.addItem(api_name, api_name)
                standalone.combo_model.setCurrentIndex(0)
                
            standalone.txt_endpoint.setText(_get_endpoint())
            standalone.txt_key.setText(_get_key())
            standalone.txt_model.setCurrentText(combo.currentText())
            
            try:
                standalone.test_result_signal.disconnect()
            except Exception:
                pass
            standalone.test_result_signal.connect(standalone._on_test_result)
            
            standalone._on_test_api()

        btn_fetch.clicked.connect(on_fetch)
        btn_test.clicked.connect(on_test)
        
        if info.get('key') in ['ai_model', 'ocr_api_model']:
            layout.addWidget(btn_fetch)
            layout.addWidget(btn_test)
            
        self.mw.widget_references[info['key']] = combo
        return container

    def create_api_manager_widget(self, info: dict) -> QWidget:
        return QWidget()

    def create_font_combobox(self, info: dict) -> QWidget:
        combo_box = SearchableComboBox()
        font_names = list(self.mw.font_map.keys())
        
        default_font = info.get("default", "Sans-serif")
        if not default_font:
            default_font = "Sans-serif"

        if default_font not in font_names:
            font_names.insert(0, default_font)

        for font in font_names:
            is_google = self.mw._get_google_font_family_from_filename(font) is not None
            display_text = font if is_google else f"{font} (Unavailable in fonts stores)"
            combo_box.addItem(display_text, userData=font)
        combo_box.addItem(INSTALL_NEW_FONT)
        combo_box.addItem(UPDATE_ALL_FONTS)

        idx = combo_box.findData(default_font)
        if idx != -1:
            combo_box.setCurrentIndex(idx)
        else:
            combo_box.setCurrentText(default_font)
            
        self.mw._last_selected_font = default_font

        self.style_custom_fonts_in_combobox(combo_box)

        def on_combo_text_changed(text):
            if text not in [INSTALL_NEW_FONT, UPDATE_ALL_FONTS]:
                actual_font = combo_box.currentData()
                if actual_font is None:
                    actual_font = text
                self.mw._last_selected_font = actual_font
                is_google = self.mw._get_google_font_family_from_filename(actual_font) is not None
                
                is_warning = not is_google
                combo_box.setProperty("warning", "true" if is_warning else "false")
                combo_box.style().unpolish(combo_box)
                combo_box.style().polish(combo_box)
                
                self.mw._on_setting_changed('font_family')

        combo_box.currentTextChanged.connect(on_combo_text_changed)
        return combo_box

    def style_custom_fonts_in_combobox(self, combo_box: QComboBox):
        for i in range(combo_box.count()):
            text = combo_box.itemText(i)
            if text not in [INSTALL_NEW_FONT, UPDATE_ALL_FONTS]:
                actual_font = combo_box.itemData(i)
                if actual_font is None:
                    actual_font = text
                is_google = self.mw._get_google_font_family_from_filename(actual_font) is not None
                if not is_google:
                    combo_box.setItemData(i, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                    
        curr_text = combo_box.currentText()
        actual_curr_font = combo_box.currentData()
        if actual_curr_font is None:
            actual_curr_font = curr_text
        is_google_curr = self.mw._get_google_font_family_from_filename(actual_curr_font) is not None
        is_warn = not is_google_curr and curr_text not in [INSTALL_NEW_FONT, UPDATE_ALL_FONTS]
        combo_box.setProperty("warning", "true" if is_warn else "false")
        combo_box.style().unpolish(combo_box)
        combo_box.style().polish(combo_box)

    def get_themed_arrow_icon_path(self, color_hex: str, theme_name: str) -> str:
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        temp_dir = os.path.join(base_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        img_path = os.path.join(temp_dir, f"arrow_{theme_name.replace(' ', '_')}.png")
        if os.path.exists(img_path):
            return img_path.replace("\\", "/")
            
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            hex_str = color_hex.lstrip('#')
            if len(hex_str) == 3:
                hex_str = "".join([c*2 for c in hex_str])
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            color = (r, g, b, 255)
            
            draw.line([(2, 4), (6, 8)], fill=color, width=2)
            draw.line([(6, 8), (10, 4)], fill=color, width=2)
            
            img.save(img_path, format="PNG")
        except Exception as e:
            print(f"Error generating arrow icon: {e}")
            
        return img_path.replace("\\", "/")

    # --- CHAIN BUILDER METHODS ---
    def create_translator_chain_builder(self, info: dict) -> QWidget:
        container = QFrame()
        container.setObjectName("ChainBuilderFrame")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        lbl_text = self.mw.get_string("ui_chain_steps") if self.mw.get_string("ui_chain_steps") != "ui_chain_steps" else info.get("label", "Translation Steps:")
        label = QLabel(lbl_text)
        label.setProperty("lang_id", "ui_chain_steps")
        label.setProperty("lang_type", "ui")
        header_layout.addWidget(label)
        header_layout.addStretch()

        add_text = self.mw.get_string("ui_chain_add") if self.mw.get_string("ui_chain_add") != "ui_chain_add" else "➕ Add Step"
        add_btn = QPushButton(add_text)
        add_btn.setProperty("lang_id", "ui_chain_add")
        add_btn.setProperty("lang_type", "ui")
        
        remove_text = self.mw.get_string("ui_chain_remove") if self.mw.get_string("ui_chain_remove") != "ui_chain_remove" else "➖ Remove Selected"
        remove_btn = QPushButton(remove_text)
        remove_btn.setProperty("lang_id", "ui_chain_remove")
        remove_btn.setProperty("lang_type", "ui")
        
        header_layout.addWidget(add_btn)
        header_layout.addWidget(remove_btn)

        container_layout.addWidget(header_widget)

        self.mw.chain_list_widget = DynamicHeightListWidget()
        self.mw.chain_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        container_layout.addWidget(self.mw.chain_list_widget)

        add_btn.clicked.connect(self.add_chain_step)
        remove_btn.clicked.connect(self.remove_chain_step)

        self.mw.widget_references[info['key']] = container
        QTimer.singleShot(0, self.update_chain_ui_state)

        return container

    def create_chain_step_widget(self) -> QWidget:
        import app.core.desktop.main_window as mw_module
        step_widget = QWidget()
        layout = QHBoxLayout(step_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        lang_combo = NoScrollComboBox()
        lang_items = [name for name, code in mw_module.LANGUAGES.items() if code != 'auto']
        lang_combo.addItems(sorted(lang_items, key=natural_sort_key))

        translator_combo = NoScrollComboBox()

        translate_to = self.mw.get_string("ui_chain_translate_to") if self.mw.get_string("ui_chain_translate_to") != "ui_chain_translate_to" else "Translate to:"
        translate_to_lbl = QLabel(translate_to)
        translate_to_lbl.setProperty("lang_id", "ui_chain_translate_to")
        translate_to_lbl.setProperty("lang_type", "ui")
        layout.addWidget(translate_to_lbl)
        layout.addWidget(lang_combo)
        
        with_text = self.mw.get_string("ui_chain_with") if self.mw.get_string("ui_chain_with") != "ui_chain_with" else "with:"
        with_lbl = QLabel(with_text)
        with_lbl.setProperty("lang_id", "ui_chain_with")
        with_lbl.setProperty("lang_type", "ui")
        layout.addWidget(with_lbl)
        layout.addWidget(translator_combo)

        setattr(step_widget, "translator_combo", translator_combo)
        setattr(step_widget, "lang_combo", lang_combo)

        lang_combo.currentTextChanged.connect(
            lambda text, tc=translator_combo: self.mw._filter_chain_step_translator_dropdown(text, tc)
        )
        self.mw._filter_chain_step_translator_dropdown(lang_combo.currentText(), translator_combo)

        handler = lambda: self.mw._on_setting_changed('translator_chain')
        translator_combo.currentTextChanged.connect(handler)
        lang_combo.currentTextChanged.connect(handler)

        return step_widget

    def add_chain_step(self):
        step_widget = self.create_chain_step_widget()

        list_item = QListWidgetItem(self.mw.chain_list_widget)
        list_item.setSizeHint(step_widget.sizeHint())

        self.mw.chain_list_widget.addItem(list_item)
        self.mw.chain_list_widget.setItemWidget(list_item, step_widget)
        self.mw._on_setting_changed('translator_chain')
        self.mw.chain_list_widget.updateGeometry()

    def remove_chain_step(self):
        selected_items = self.mw.chain_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            row = self.mw.chain_list_widget.row(item)
            self.mw.chain_list_widget.takeItem(row)
        self.mw._on_setting_changed('translator_chain')
        self.mw.chain_list_widget.updateGeometry()

    def get_translator_chain_string(self) -> str:
        import app.core.desktop.main_window as mw_module
        if not hasattr(self.mw, 'chain_list_widget'):
            return ""

        steps = []
        for i in range(self.mw.chain_list_widget.count()):
            item = self.mw.chain_list_widget.item(i)
            widget = self.mw.chain_list_widget.itemWidget(item)

            if widget and hasattr(widget, 'translator_combo') and hasattr(widget, 'lang_combo'):
                translator_name = widget.translator_combo.currentData()
                if not translator_name:
                    translator_name = widget.translator_combo.currentText()
                lang_name = widget.lang_combo.currentText()

                if translator_name not in mw_module.TRANSLATOR_GROUPS:
                    lang_code = mw_module.LANGUAGES.get(lang_name, '')
                    if lang_code:
                        steps.append(f"{translator_name}:{lang_code}")

        return ";".join(steps)

    def rebuild_chain_from_string(self, chain_string: str):
        import app.core.desktop.main_window as mw_module
        self.mw.chain_list_widget.clear()
        if not chain_string:
            return

        steps = chain_string.split(';')
        code_to_lang_name = {v: k for k, v in mw_module.LANGUAGES.items()}

        for step in steps:
            parts = step.split(':')
            if len(parts) == 2:
                translator_name, lang_code = parts

                step_widget = self.create_chain_step_widget()
                list_item = QListWidgetItem(self.mw.chain_list_widget)
                list_item.setSizeHint(step_widget.sizeHint())
                self.mw.chain_list_widget.addItem(list_item)
                self.mw.chain_list_widget.setItemWidget(list_item, step_widget)

                lang_name = code_to_lang_name.get(lang_code, "")
                if lang_name:
                    getattr(step_widget, "lang_combo").setCurrentText(lang_name)
                
                # Manual inline combobox setting
                combo_box = getattr(step_widget, "translator_combo")
                index = -1
                for i in range(combo_box.count()):
                    if combo_box.itemData(i) == translator_name:
                        index = i
                        break
                if index != -1:
                    combo_box.setCurrentIndex(index)
                else:
                    combo_box.setCurrentText(translator_name)

        self.mw.chain_list_widget.updateGeometry()

    def update_chain_ui_state(self):
        if hasattr(self.mw, 'chain_list_widget'):
            enable_chain = getattr(self.mw, 'chain_list_widget_enabled', False)
            self.mw.chain_list_widget.setEnabled(enable_chain)
            self.update_chain_list_height()
            
    def update_chain_list_height(self):
        if not hasattr(self.mw, 'chain_list_widget'):
            return
        self.mw.chain_list_widget.updateGeometry()
