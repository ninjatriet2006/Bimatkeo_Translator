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
                               QPushButton, QComboBox, QLabel, QMessageBox, QGroupBox)
from PySide6.QtCore import Qt, QMetaObject, Q_ARG
from app.core.shared_registry import TranslatorFactory

class TranslatorStandaloneWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.translator_instance = None
        self._setup_ui()
        self._populate_models()

    def _setup_ui(self):
        self.layout_obj = QVBoxLayout(self)
        
        # Config Area
        group_config = QGroupBox("Configuration")
        layout_config = QHBoxLayout(group_config)
        
        self.combo_model = QComboBox()
        self.btn_load = QPushButton("Load Model")
        self.btn_load.clicked.connect(self._on_load_model)
        
        layout_config.addWidget(QLabel("Translator Model:"))
        layout_config.addWidget(self.combo_model, stretch=1)
        layout_config.addWidget(self.btn_load)
        self.layout_obj.addWidget(group_config)

        # Translation Area
        group_trans = QGroupBox("Translation")
        layout_trans = QVBoxLayout(group_trans)
        
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

    def _populate_models(self):
        factories = TranslatorFactory.get_registered_providers()
        for key in factories:
            self.combo_model.addItem(TranslatorFactory.get_display_name(key), key)

    def _on_load_model(self):
        key = self.combo_model.currentData()
        if not key:
            return
            
        self.btn_load.setEnabled(False)
        self.btn_load.setText("Loading...")
        
        def _load():
            try:
                # Need dummy config dict. For a standalone UI, we might need a basic config
                config_dict = {"translator": {"model": key}}
                
                # Fetch project root to resolve paths
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
                os.environ["PROJECT_ROOT"] = project_root
                
                from app.core.translator.initializer import TranslatorInitializer
                chained, editor = TranslatorInitializer.initialize(config_dict, project_root, {}, log_callback=None)
                
                if chained and len(chained) > 0:
                    self.translator_instance = chained[0]
                    QMetaObject.invokeMethod(self, "_on_load_success", Qt.ConnectionType.QueuedConnection)
                else:
                    raise Exception("Failed to load translator")
                    
            except Exception as e:
                QMetaObject.invokeMethod(self, "_on_load_fail", Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(e)))

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
                result = self.translator_instance.translate(source_text)
                QMetaObject.invokeMethod(self, "_on_trans_success", Qt.ConnectionType.QueuedConnection, Q_ARG(str, result))
            except Exception as e:
                QMetaObject.invokeMethod(self, "_on_trans_fail", Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(e)))

        threading.Thread(target=_trans, daemon=True).start()

    def _on_trans_success(self, text: str):
        self.txt_target.setPlainText(text)
        self.btn_translate.setEnabled(True)
        self.btn_translate.setText("Translate")

    def _on_trans_fail(self, error_msg: str):
        self.btn_translate.setEnabled(True)
        self.btn_translate.setText("Translate")
        QMessageBox.critical(self, "Error", f"Translation failed:\n{error_msg}")
