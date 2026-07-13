"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.ui_dropdown_manager
- RESPONSIBILITY: Handle dropdown dynamic lists (e.g., model combo boxes) and UI length labels.
- CALLED BY: app.core.desktop.logic.core_handlers.ui_dropdowns
- CALLS TO: PySide6.QtWidgets, PySide6.QtGui
- IN = OUT: Manipulates QComboBox items based on current settings and natural sorting.
=============================================================================
"""
from PySide6.QtWidgets import QComboBox
from PySide6.QtGui import QColor
from PySide6.QtCore import Qt
import re

def natural_sort_key(s):
    return [int(text) if text.isdigit() else text.lower() for text in re.split(r'(\d+)', s)]

class UIDropdownManager:
    def __init__(self, main_window):
        self.mw = main_window

    def update_max_length_label(self):
        from app.core.shared_registry import TranslatorFactory
        from app.core.translator.utils import PromptBuilder
        
        translator_name = self.mw._get_active_translator_name()
        max_chars = -1
        try:
            translator_class = TranslatorFactory.get_class(translator_name)
            if translator_class and hasattr(translator_class, 'MAX_CHARS'):
                max_chars = translator_class.MAX_CHARS
        except Exception:
            pass
            
        sys_prompt_len = 0
        sys_profile = self.mw.current_settings.get('system_prompt_profile', 'example')
        if sys_profile and sys_profile != "None":
            project_base = getattr(self.mw.config_loader, 'project_base_dir', "")
            if not project_base:
                import os
                project_base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            builder = PromptBuilder(project_base, sys_profile)
            tgt_lang = self.mw.current_settings.get('target_lang', 'ENG')
            sys_prompt_len = len(builder.build_prompt("auto", tgt_lang))
            
        if max_chars > 0:
            available = max_chars - sys_prompt_len
            label_text = f"Max Request Length (Max: {available} chars):"
        else:
            label_text = "Max Request Length (Max: -1 chars):"
            
        if hasattr(self.mw, 'setting_labels') and 'max_request_length' in self.mw.setting_labels:
            self.mw.setting_labels['max_request_length'].setText(label_text)

    def on_translator_changed(self, translator_name: str):
        lang_data = self.mw.config_loader.get_lang_data(self.mw.config_loader.app_language)
        ui_strings = lang_data.get("ui_strings", {})
        if translator_name == ui_strings.get("update_supported_langs", "📥 Update translation support list..."):
            return
        if translator_name:
            translator_name = translator_name.split(" (Not Setup)")[0].split(" (Incomplete)")[0]
        self.mw._update_translator_tooltip(translator_name)

    def is_translator_supported_for_target(self, translator_name: str, target_code: str) -> bool:
        from app.core.shared_registry import TranslatorFactory
        if translator_name in ["none", "original"]:
            return True
        capabilities = TranslatorFactory.get_capabilities(translator_name)
        if capabilities.get('__any__') == '__all__':
            return True
        for source_lang, target_langs in capabilities.items():
            if target_code in target_langs:
                return True
        return False

    def filter_translator_dropdowns(self, target_lang_name: str, context_key: str | None = None):
        import app.core.desktop.main_window as mw_module
        if not target_lang_name:
            return

        target_code = mw_module.LANGUAGES.get(target_lang_name)
        if not target_code:
            return

        if context_key:
            offline_combo = self.mw.task_widgets.get(context_key, {}).get('offline_translator')
        else:
            offline_combo = self.mw.setting_widgets.get('offline_translator')
            
        if offline_combo:
            current_val = offline_combo.currentData()
            offline_combo.blockSignals(True)
            offline_combo.clear()
            offline_combo.addItem("--- Select ---", "none")
            
            setup_items = []
            not_setup_items = []
            for val in self.mw.original_offline_translators:
                supported = self.is_translator_supported_for_target(val, target_code)
                state = self.mw.config_loader.get_model_state(val, field='offline_translator')
                
                label = self.mw.config_loader.format_display_label(val, 'offline_translator')
                if state == "NOT_SETUP":
                    label += " (Not Setup)"
                elif state == "INCOMPLETE":
                    label += " (Incomplete)"
                if not supported:
                    label += " (Unavailable for this language)"
                    
                if state == "OK":
                    setup_items.append((val, label, not supported))
                else:
                    not_setup_items.append((val, label, not supported))
            
            setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            not_setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            
            for val, label, is_unsupported in setup_items:
                offline_combo.addItem(label, val)
                if is_unsupported:
                    last_idx = offline_combo.count() - 1
                    offline_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                    
            for val, label, is_unsupported in not_setup_items:
                offline_combo.addItem(label, val)
                last_idx = offline_combo.count() - 1
                offline_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                
            lang_data = self.mw.config_loader.get_lang_data(self.mw.config_loader.app_language)
            ui_strings = lang_data.get("ui_strings", {})
            update_langs_text = ui_strings.get("update_supported_langs", "📥 Update translation support list...")
            update_software_text = ui_strings.get("update_all_models", "📥 Update ALL {category} models...").replace("{category}", "software")
            
            offline_combo.addItem(update_langs_text, "update_trigger")
            offline_combo.addItem(update_software_text, "update_software_trigger")
            
            restored = False
            for i in range(offline_combo.count()):
                if offline_combo.itemData(i) == current_val:
                    offline_combo.setCurrentIndex(i)
                    restored = True
                    break
            if not restored and offline_combo.count() > 0:
                offline_combo.setCurrentIndex(0)
            offline_combo.blockSignals(False)
            self.mw._on_setting_changed('offline_translator', context_key)

        if context_key:
            ai_combo = self.mw.task_widgets.get(context_key, {}).get('ai_translator')
        else:
            ai_combo = self.mw.setting_widgets.get('ai_translator')
            
        if ai_combo:
            current_val = ai_combo.currentData()
            ai_combo.blockSignals(True)
            ai_combo.clear()
            ai_combo.addItem("--- Select ---", "none")
            setup_items = []
            not_setup_items = []
            for val in self.mw.original_ai_translators:
                supported = self.is_translator_supported_for_target(val, target_code)
                state = self.mw.config_loader.get_model_state(val, field='ai_translator')
                
                label = self.mw.config_loader.format_display_label(val, 'ai_translator')
                if state == "NOT_SETUP":
                    label += " (Not Setup)"
                elif state == "INCOMPLETE":
                    label += " (Incomplete)"
                if not supported:
                    label += " (Unavailable for this language)"
                    
                if state == "OK":
                    setup_items.append((val, label, not supported))
                else:
                    not_setup_items.append((val, label, not supported))
            
            setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            not_setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            
            for val, label, is_unsupported in setup_items:
                ai_combo.addItem(label, val)
                if is_unsupported:
                    last_idx = ai_combo.count() - 1
                    ai_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                    
            for val, label, is_unsupported in not_setup_items:
                ai_combo.addItem(label, val)
                last_idx = ai_combo.count() - 1
                ai_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                
            lang_data = self.mw.config_loader.get_lang_data(self.mw.config_loader.app_language)
            ui_strings = lang_data.get("ui_strings", {})
            update_langs_text = ui_strings.get("update_supported_langs", "📥 Update translation support list...")
            update_software_text = ui_strings.get("update_all_models", "📥 Update ALL {category} models...").replace("{category}", "software")

            ai_combo.addItem(update_langs_text, "update_trigger")
            ai_combo.addItem(update_software_text, "update_software_trigger")
            
            restored = False
            for i in range(ai_combo.count()):
                if ai_combo.itemData(i) == current_val:
                    ai_combo.setCurrentIndex(i)
                    restored = True
                    break
            if not restored and ai_combo.count() > 0:
                ai_combo.setCurrentIndex(0)
            ai_combo.blockSignals(False)
            self.mw._on_setting_changed('ai_translator', context_key)

        self.mw._update_translator_visibility()
        self.mw._update_ocr_visibility()
        self.mw._update_inpainter_visibility()
        active_translator = self.mw._get_active_translator_name()
        self.mw._update_translator_tooltip(active_translator)

    def filter_chain_step_translator_dropdown(self, target_lang_name: str, translator_combo: QComboBox):
        import app.core.desktop.main_window as mw_module
        if not target_lang_name:
            return
        
        target_code = mw_module.LANGUAGES.get(target_lang_name)
        if not target_code:
            return

        current_val = translator_combo.currentData()
        translator_combo.blockSignals(True)
        translator_combo.clear()

        for group_name, translators in mw_module.TRANSLATOR_GROUPS.items():
            field_name = "offline_translator" if "OFFLINE" in group_name else ("ai_translator" if "API" in group_name else None)
            
            setup_items = []
            not_setup_items = []
            for t in translators:
                supported = self.is_translator_supported_for_target(t, target_code)
                state = self.mw.config_loader.get_model_state(t, field=field_name)
                
                label = self.mw.config_loader.format_display_label(t, field_name)
                if state == "NOT_SETUP":
                    label += " (Not Setup)"
                elif state == "INCOMPLETE":
                    label += " (Incomplete)"
                if not supported:
                    label += " (Unavailable for this language)"
                    
                if state == "OK":
                    setup_items.append((t, label, not supported))
                else:
                    not_setup_items.append((t, label, not supported))
                    
            setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            not_setup_items.sort(key=lambda x: natural_sort_key(x[0]))
            
            if not setup_items and not not_setup_items:
                continue
            
            item_index = translator_combo.count()
            translator_combo.addItem(group_name)
            translator_combo.model().item(item_index).setEnabled(False)  # type: ignore
            
            for t, label, is_unsupported in setup_items:
                translator_combo.addItem(label, t)
                if is_unsupported:
                    last_idx = translator_combo.count() - 1
                    translator_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            for t, label, is_unsupported in not_setup_items:
                translator_combo.addItem(label, t)
                last_idx = translator_combo.count() - 1
                translator_combo.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
        
        restored = False
        for i in range(translator_combo.count()):
            if translator_combo.itemData(i) == current_val:
                translator_combo.setCurrentIndex(i)
                restored = True
                break
        if not restored and translator_combo.count() > 0:
            for i in range(translator_combo.count()):
                if translator_combo.model().item(i).isEnabled():  # type: ignore
                    translator_combo.setCurrentIndex(i)
                    break
        translator_combo.blockSignals(False)

    def on_target_lang_changed(self, target_lang_name: str):
        lang_data = self.mw.config_loader.get_lang_data(self.mw.config_loader.app_language)
        ui_strings = lang_data.get("ui_strings", {})
        if target_lang_name == ui_strings.get("update_langs_list", "📥 Update language list..."):
            return
        self.filter_translator_dropdowns(target_lang_name)

    def filter_language_dropdown(self, translator_name: str, lang_combo: QComboBox):
        import app.core.desktop.main_window as mw_module
        if not lang_combo:
            return

        if translator_name:
            translator_name = translator_name.split(" (Not Setup)")[0].split(" (Incomplete)")[0]

        from app.core.shared_registry import TranslatorFactory
        capabilities = TranslatorFactory.get_capabilities(translator_name)
        supported_codes = set()

        if capabilities.get('__any__') == '__all__':
            all_langs = list(mw_module.LANGUAGES.values())
            if "auto" in all_langs:
                all_langs.remove("auto")
            supported_codes = set(all_langs)
        else:
            for source_lang, target_langs in capabilities.items():
                supported_codes.update(target_langs)

        supported_display_names = [name for name, code in mw_module.LANGUAGES.items() if code in supported_codes]
        current_selection = lang_combo.currentText()

        lang_combo.blockSignals(True)
        lang_combo.clear()
        lang_combo.addItem("--- Select ---", "none")
        if not supported_display_names:
            lang_combo.addItem("No Supported Targets")
            lang_combo.setEnabled(False)
        else:
            for name in sorted(supported_display_names):
                lang_combo.addItem(name, mw_module.LANGUAGES[name])
            lang_combo.setEnabled(True)
        lang_combo.blockSignals(False)

        if current_selection == "--- Select ---" or current_selection == "none":
            lang_combo.setCurrentIndex(0)
        elif current_selection in supported_display_names:
            lang_combo.setCurrentText(current_selection)
        else:
            lang_combo.setCurrentIndex(0)
