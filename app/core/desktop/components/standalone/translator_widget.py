"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.standalone.translator_widget
- RESPONSIBILITY: Standalone UI for Translator plugin.
- CALLED BY: app.core.desktop.standalone_runner
- CALLS TO: app.core.shared_registry.base
- IN = OUT: Translates text.
=============================================================================
"""
import os
import threading
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QPushButton, QComboBox, QLabel, QMessageBox, QGroupBox, QLineEdit)
from PySide6.QtCore import Qt, QMetaObject, Q_ARG, Signal
from app.core.shared_registry import TranslatorFactory

class TranslatorStandaloneWidget(QWidget):
    log_signal = Signal(str, str)
    load_success_signal = Signal()
    load_fail_signal = Signal(str)
    trans_success_signal = Signal(str)
    trans_fail_signal = Signal(str)
    fetch_success_signal = Signal(list)
    fetch_fail_signal = Signal(str)
    test_result_signal = Signal(bool, str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.translator_instance = None
        
        self.log_signal.connect(self._on_log)
        self.load_success_signal.connect(self._on_load_success)
        self.load_fail_signal.connect(self._on_load_fail)
        self.trans_success_signal.connect(self._on_trans_success)
        self.trans_fail_signal.connect(self._on_trans_fail)
        self.fetch_success_signal.connect(self._on_fetch_success)
        self.fetch_fail_signal.connect(self._on_fetch_fail)
        self.test_result_signal.connect(self._on_test_result)
        
        self._setup_ui()
        self._populate_models()

    def _setup_ui(self):
        self.layout_obj = QVBoxLayout(self)
        
        # Config Area
        group_config = QGroupBox("Configuration")
        layout_config = QVBoxLayout(group_config)
        
        self.combo_category = QComboBox()
        self.combo_category.addItems(["Offline", "Online"])
        self.combo_category.currentTextChanged.connect(self._on_category_changed)
        
        self.combo_model = QComboBox()
        self.combo_model.currentIndexChanged.connect(self._on_profile_selected)
        
        layout_config_top = QHBoxLayout()
        layout_config_top.addWidget(QLabel("Category:"))
        layout_config_top.addWidget(self.combo_category)
        layout_config_top.addWidget(QLabel("Model/Profile:"))
        layout_config_top.addWidget(self.combo_model, stretch=1)
        
        layout_config.addLayout(layout_config_top)
        
        # Extended config fields (Online APIs)
        self.extended_config_widget = QWidget()
        self.extended_config_layout = QVBoxLayout(self.extended_config_widget)
        self.extended_config_layout.setContentsMargins(0, 0, 0, 0)
        
        row1 = QHBoxLayout()
        self.combo_sys_prompt = QComboBox()
        row1.addWidget(QLabel("Sys Prompt:"))
        row1.addWidget(self.combo_sys_prompt, stretch=1)
        
        row2 = QHBoxLayout()
        self.txt_endpoint = QLineEdit()
        row2.addWidget(QLabel("Endpoint:"))
        row2.addWidget(self.txt_endpoint, stretch=1)
        
        row3 = QHBoxLayout()
        self.txt_model = QComboBox()
        self.txt_model.setEditable(True)
        row3.addWidget(QLabel("Model:"))
        row3.addWidget(self.txt_model, stretch=1)
        
        self.btn_fetch = QPushButton("Fetch")
        self.btn_fetch.setFixedWidth(50)
        self.btn_fetch.clicked.connect(self._on_fetch_models)
        row3.addWidget(self.btn_fetch)
        
        self.btn_test = QPushButton("Test")
        self.btn_test.setFixedWidth(50)
        self.btn_test.clicked.connect(self._on_test_api)
        row3.addWidget(self.btn_test)
        
        row4 = QHBoxLayout()
        self.txt_key = QLineEdit()
        self.txt_key.setEchoMode(QLineEdit.EchoMode.Password)
        row4.addWidget(QLabel("Key:"))
        row4.addWidget(self.txt_key, stretch=1)
        
        self.extended_config_layout.addLayout(row1)
        self.extended_config_layout.addLayout(row2)
        self.extended_config_layout.addLayout(row3)
        self.extended_config_layout.addLayout(row4)
        
        layout_config.addWidget(self.extended_config_widget)
        
        self.btn_load = QPushButton("Load Model")
        self.btn_load.clicked.connect(self._on_load_model)
        layout_config.addWidget(self.btn_load)
        
        self.layout_obj.addWidget(group_config)

        # Translation Area
        group_trans = QGroupBox("Translation")
        layout_trans = QVBoxLayout(group_trans)
        
        # Languages Area
        layout_langs = QHBoxLayout()
        self.combo_src_lang = QComboBox()
        self.combo_tgt_lang = QComboBox()
        layout_langs.addWidget(QLabel("Source:"))
        layout_langs.addWidget(self.combo_src_lang)
        layout_langs.addWidget(QLabel("Target:"))
        layout_langs.addWidget(self.combo_tgt_lang)
        layout_trans.addLayout(layout_langs)
        
        self.txt_source = QTextEdit()
        self.txt_source.setPlaceholderText("Enter source text here...")
        layout_trans.addWidget(QLabel("Source Text:"))
        layout_trans.addWidget(self.txt_source)
        
        self.btn_translate = QPushButton("Translate")
        self.btn_translate.setEnabled(False)
        self.btn_translate.clicked.connect(self._on_translate)
        layout_trans.addWidget(self.btn_translate)
        
        self.txt_target = QTextEdit()
        self.txt_target.setPlaceholderText("Translated text will appear here...")
        self.txt_target.setReadOnly(True)
        layout_trans.addWidget(QLabel("Target Text:"))
        layout_trans.addWidget(self.txt_target)
        
        self.layout_obj.addWidget(group_trans)
        
        # Console Area
        group_console = QGroupBox("Console Logs")
        layout_console = QVBoxLayout(group_console)
        self.txt_console = QTextEdit()
        self.txt_console.setReadOnly(True)
        self.txt_console.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: monospace;")
        layout_console.addWidget(self.txt_console)
        self.layout_obj.addWidget(group_console)

    def _log(self, level: str, msg: str):
        self.log_signal.emit(level, msg)

    def _on_log(self, level: str, msg: str):
        self.txt_console.append(f"[{level}] {msg}")

    def _get_api_profiles(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
        path = os.path.join(project_root, ".config", "configs", "api_profiles.yaml")
        if os.path.exists(path):
            import yaml
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    return yaml.safe_load(f) or {}
            except:
                pass
        return {}

    def _on_category_changed(self, category: str):
        self._populate_models(category)

    def _populate_models(self, category: str = "Offline"):
        self.combo_model.clear()
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
        
        if category == "Offline":
            from app.core.desktop.config import ConfigLoader
            config_loader = ConfigLoader(project_root)
            
            keys = config_loader.list_field_keys("offline_translator")
            for key in keys:
                label = config_loader.format_display_label(key, "offline_translator")
                state = config_loader.get_model_state(key, "offline_translator")
                if state == "NOT_SETUP":
                    label += " (Not Setup)"
                elif state == "INCOMPLETE":
                    label += " (Incomplete)"
                self.combo_model.addItem(label, key)
        else:
            profiles = self._get_api_profiles()
            for prof_name, prof_data in profiles.items():
                if isinstance(prof_data, dict) and prof_data.get("type") != "Pool":
                    provider = prof_data.get("provider", "openai")
                    label = f"{prof_name} ({provider})"
                    self.combo_model.addItem(label, prof_name)
                    
        # Load languages
        self.combo_src_lang.clear()
        self.combo_tgt_lang.clear()
        import app.core.desktop.main_window as mw_module
        if mw_module.LANGUAGES:
            self.combo_src_lang.addItem("Auto-Detect", "auto")
            for name, code in sorted(mw_module.LANGUAGES.items()):
                if code != "auto":
                    self.combo_src_lang.addItem(name, code)
                    self.combo_tgt_lang.addItem(name, code)
            
            # Default to Auto -> Vietnamese if available
            self.combo_src_lang.setCurrentIndex(0)
            tgt_idx = self.combo_tgt_lang.findData("VIN")
            if tgt_idx >= 0:
                self.combo_tgt_lang.setCurrentIndex(tgt_idx)
                
        # Load system prompts
        self.combo_sys_prompt.clear()
        prompt_path = os.path.join(project_root, ".config", "configs", "system_prompt.yaml")
        if os.path.exists(prompt_path):
            import yaml
            try:
                with open(prompt_path, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                    if data and "profiles" in data:
                        for p in data["profiles"].keys():
                            self.combo_sys_prompt.addItem(p)
            except:
                pass

    def _on_profile_selected(self):
        category = self.combo_category.currentText()
        if category == "Online":
            key = self.combo_model.currentData()
            if key:
                profiles = self._get_api_profiles()
                prof_data = profiles.get(key, {})
                self.txt_endpoint.setText(prof_data.get("endpoint", ""))
                self.txt_model.setCurrentText(prof_data.get("model", ""))
                self.txt_key.setText(prof_data.get("key", ""))
            
            self.extended_config_widget.setVisible(True)
        else:
            self.extended_config_widget.setVisible(False)

    def _on_load_model(self):
        key = self.combo_model.currentData()
        if not key:
            return
            
        self.btn_load.setEnabled(False)
        self.btn_load.setText("Loading...")
        
        def _load():
            from PySide6.QtCore import QMetaObject, Qt
            try:
                # Fetch project root to resolve paths
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
                os.environ["PROJECT_ROOT"] = project_root
                
                category = self.combo_category.currentText()
                sys_prompt = self.combo_sys_prompt.currentText() or "None"
                
                if category == "Offline":
                    config_dict = {
                        "translator": {
                            "translator_category": "Offline",
                            "translator": key,
                            "system_prompt_profile": sys_prompt
                        }
                    }
                else:
                    profiles = self._get_api_profiles()
                    prof_data = profiles.get(key, {})
                    endpoint = self.txt_endpoint.text().strip() or prof_data.get("endpoint", "")
                    model = self.txt_model.currentText().strip() or prof_data.get("model", "")
                    api_key = self.txt_key.text().strip() or prof_data.get("key", "")
                    
                    if not model or not api_key or (not endpoint and prof_data.get("provider") != "gemini"):
                        raise ValueError(f"Thiếu tham số cấu hình cho API Online. Vui lòng nhập đầy đủ Endpoint (trừ Gemini), Model và API Key cho profile '{key}'.")
                        
                    config_dict = {
                        "translator": {
                            "translator_category": "Online",
                            "translator": prof_data.get("provider", "openai"),
                            "ai_endpoint": endpoint,
                            "ai_model": model,
                            "ai_api_key": api_key,
                            "system_prompt_profile": sys_prompt
                        }
                    }
                
                from app.core.translator.initializer import TranslatorInitializer
                chained, editor = TranslatorInitializer.initialize(config_dict, project_root, {}, log_callback=self._log)
                
                if chained and len(chained) > 0:
                    self.translator_instance = chained[0][0]
                    self.load_success_signal.emit()
                else:
                    raise Exception("Failed to load translator")
                    
            except Exception as e:
                err = str(e)
                self.load_fail_signal.emit(err)

        threading.Thread(target=_load, daemon=True).start()

    def _on_load_success(self):
        self.btn_load.setText("Loaded")
        self.btn_translate.setEnabled(True)
        QMessageBox.information(self, "Success", "Model loaded successfully!")

    def _on_load_fail(self, error_msg: str):
        self.btn_load.setEnabled(True)
        self.btn_load.setText("Load Model")
        QMessageBox.critical(self, "Error", f"Failed to load model:\n{error_msg}")

    def _on_translate(self):
        if not self.translator_instance:
            return
            
        source_text = self.txt_source.toPlainText().strip()
        if not source_text:
            return
            
        self.btn_translate.setEnabled(False)
        self.btn_translate.setText("Translating...")
        
        def _trans():
            try:
                src_lang = self.combo_src_lang.currentData() or "auto"
                tgt_lang = self.combo_tgt_lang.currentData() or "VIN"
                # BaseTranslator interface: translate(texts: List[str], src_lang: str, tgt_lang: str, context_texts: List[str] | None = None)
                results = self.translator_instance.translate([source_text], src_lang, tgt_lang)
                
                if results and len(results) > 0:
                    res = results[0]
                    final_text = res.get("text", "") if isinstance(res, dict) else str(res)
                else:
                    final_text = ""
                
                self.trans_success_signal.emit(final_text)
            except Exception as e:
                self.trans_fail_signal.emit(str(e))

        threading.Thread(target=_trans, daemon=True).start()

    def _on_trans_success(self, text: str):
        self.txt_target.setPlainText(text)
        self.btn_translate.setEnabled(True)
        self.btn_translate.setText("Translate")

    def _on_trans_fail(self, error_msg: str):
        self.btn_translate.setEnabled(True)
        self.btn_translate.setText("Translate")
        QMessageBox.critical(self, "Error", f"Translation failed:\n{error_msg}")

    def _on_fetch_models(self):
        key_profile = self.combo_model.currentData()
        if not key_profile:
            return
            
        profiles = self._get_api_profiles()
        prof_data = profiles.get(key_profile, {})
        ai_provider = prof_data.get("provider", "openai")
        
        endpoint = self.txt_endpoint.text().strip() or prof_data.get("endpoint", "")
        key = self.txt_key.text().strip() or prof_data.get("key", "")
        
        if not endpoint and ai_provider != 'gemini':
            QMessageBox.warning(self, "Warning", "No API Endpoint URL provided. Please enter a valid URL.")
            return

        self.btn_fetch.setEnabled(False)
        self.btn_fetch.setText("...")

        def _fetch():
            from app.core.api.manager import fetch_remote_ai_models
            try:
                models = fetch_remote_ai_models(endpoint, key, ai_provider)
                self.fetch_success_signal.emit(models)
            except Exception as e:
                self.fetch_fail_signal.emit(str(e))

        threading.Thread(target=_fetch, daemon=True).start()

    def _on_fetch_success(self, models: list):
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("Fetch")
        if models:
            current_text = self.txt_model.currentText()
            self.txt_model.clear()
            self.txt_model.addItem("Auto")
            self.txt_model.addItems(models)
            if current_text and (current_text in models or current_text == "Auto"):
                self.txt_model.setCurrentText(current_text)
            else:
                self.txt_model.setCurrentText("Auto")
            QMessageBox.information(self, "Success", f"Fetched {len(models)} models successfully.")
        else:
            QMessageBox.warning(self, "Warning", "No models found.")

    def _on_fetch_fail(self, error_msg: str):
        self.btn_fetch.setEnabled(True)
        self.btn_fetch.setText("Fetch")
        QMessageBox.critical(self, "Error", f"Failed to fetch models:\n{error_msg}")

    def _on_test_api(self):
        key_profile = self.combo_model.currentData()
        if not key_profile:
            return
            
        profiles = self._get_api_profiles()
        prof_data = profiles.get(key_profile, {})
        ai_provider = prof_data.get("provider", "openai")
        
        endpoint = self.txt_endpoint.text().strip() or prof_data.get("endpoint", "")
        key = self.txt_key.text().strip() or prof_data.get("key", "")
        model_name = self.txt_model.currentText().strip() or prof_data.get("model", "")
        
        if not model_name or model_name == "Auto":
            QMessageBox.warning(self, "Warning", "Please select a specific model to test.")
            return

        if not endpoint and ai_provider != 'gemini':
            QMessageBox.warning(self, "Warning", "No API Endpoint URL provided.")
            return

        self.btn_test.setEnabled(False)
        self.btn_test.setText("...")

        def _test():
            from app.core.shared_registry import TranslatorFactory
            try:
                import app.plugins.translator.openai.main_impl
                import app.plugins.translator.gemini.main_impl
                import app.plugins.translator.felo.main_impl
                
                translator = TranslatorFactory.create(ai_provider)
                translator.load_weights({
                    "endpoint": endpoint,
                    "key": key,
                    "model": model_name
                })
                success, msg = translator.test_connection()
                self.test_result_signal.emit(success, msg)
            except Exception as e:
                self.test_result_signal.emit(False, str(e))

        threading.Thread(target=_test, daemon=True).start()

    def _on_test_result(self, success: bool, message: str):
        self.btn_test.setEnabled(True)
        self.btn_test.setText("Test")
        if success:
            QMessageBox.information(self, "Success", message)
        else:
            QMessageBox.critical(self, "Error", message)
