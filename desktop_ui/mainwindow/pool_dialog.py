from desktop_ui.mainwindow.widgets_helper import SearchableComboBox
from PySide6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QListWidget, QComboBox,
                               QMessageBox, QGroupBox, QFormLayout, QWidget)
from PySide6.QtCore import Qt, Signal
import threading
import json
import urllib.request
import urllib.error
import ssl

class ManagePoolsDialog(QDialog):
    models_fetched_signal = Signal(list)
    fetch_finished_signal = Signal()

    def __init__(self, main_window):
        super().__init__(main_window)
        self.main_window = main_window
        self.setWindowTitle("Manage API Pools")
        self.resize(500, 600)
        
        # Load data
        self.pools = self.main_window._load_pool_profiles()
        self.api_profiles = self.main_window._load_api_profiles()
        
        self._build_ui()
        self._refresh_pool_selector()
        
        self.models_fetched_signal.connect(self._show_fetched_models)
        self.fetch_finished_signal.connect(self._on_fetch_finished)
        
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # --- Top: Pool Selection / Creation ---
        pool_sel_layout = QHBoxLayout()
        pool_sel_layout.addWidget(QLabel("Select Pool:"))
        self.pool_combo = SearchableComboBox()
        self.pool_combo.currentTextChanged.connect(self._on_pool_changed)
        pool_sel_layout.addWidget(self.pool_combo, stretch=1)
        
        self.add_pool_btn = QPushButton("+")
        self.add_pool_btn.setFixedWidth(30)
        self.add_pool_btn.setToolTip("Create a new pool")
        self.add_pool_btn.clicked.connect(self._create_new_pool)
        pool_sel_layout.addWidget(self.add_pool_btn)
        
        self.delete_pool_btn = QPushButton("-")
        self.delete_pool_btn.setFixedWidth(30)
        self.delete_pool_btn.setToolTip("Delete this pool")
        self.delete_pool_btn.clicked.connect(self._delete_pool)
        pool_sel_layout.addWidget(self.delete_pool_btn)
        
        layout.addLayout(pool_sel_layout)
        
        # --- Middle: API List for the current pool ---
        self.api_list = QListWidget()
        layout.addWidget(QLabel("APIs in Pool (Ordered by Priority):"))
        layout.addWidget(self.api_list)
        
        list_controls_layout = QHBoxLayout()
        self.up_btn = QPushButton("Move Up")
        self.up_btn.clicked.connect(lambda: self._move_item(-1))
        self.down_btn = QPushButton("Move Down")
        self.down_btn.clicked.connect(lambda: self._move_item(1))
        self.remove_api_btn = QPushButton("Remove from Pool")
        self.remove_api_btn.clicked.connect(self._remove_from_pool)
        
        list_controls_layout.addWidget(self.up_btn)
        list_controls_layout.addWidget(self.down_btn)
        list_controls_layout.addStretch()
        list_controls_layout.addWidget(self.remove_api_btn)
        layout.addLayout(list_controls_layout)
        
        # --- Bottom: Add API to Pool ---
        add_group = QGroupBox("Add API to Pool")
        add_layout = QVBoxLayout()
        
        # Existing API
        existing_layout = QHBoxLayout()
        existing_layout.addWidget(QLabel("Add Existing API:"))
        self.existing_api_combo = QComboBox()
        self.existing_api_combo.addItems(list(self.api_profiles.keys()))
        existing_layout.addWidget(self.existing_api_combo, stretch=1)
        
        self.add_existing_btn = QPushButton("Add")
        self.add_existing_btn.clicked.connect(self._add_existing_to_pool)
        existing_layout.addWidget(self.add_existing_btn)
        add_layout.addLayout(existing_layout)
        
        add_layout.addWidget(QLabel("--- OR Add New API ---", alignment=Qt.AlignmentFlag.AlignCenter))
        
        # New API
        form_layout = QFormLayout()
        self.new_api_name = QLineEdit()
        # self.new_api_provider is completely removed as requested by the user.
        self.new_api_endpoint = QLineEdit()
        
        self.new_api_model = SearchableComboBox()
        self.new_api_model.setEditable(True)
        self.new_api_model.addItem("Auto")
        self.new_api_model.setCurrentText("Auto")
        
        model_layout = QHBoxLayout()
        model_layout.setContentsMargins(0,0,0,0)
        model_layout.addWidget(self.new_api_model, stretch=1)
        self.fetch_models_btn = QPushButton("Fetch")
        self.fetch_models_btn.setFixedWidth(50)
        self.fetch_models_btn.setToolTip("Fetch Models")
        self.fetch_models_btn.clicked.connect(self._fetch_models)
        model_layout.addWidget(self.fetch_models_btn)
        
        model_container = QWidget()
        model_container.setLayout(model_layout)
        
        self.new_api_key = QLineEdit()
        self.new_api_key.setEchoMode(QLineEdit.EchoMode.Password)
        
        form_layout.addRow("API Name:", self.new_api_name)
        form_layout.addRow("Endpoint URL:", self.new_api_endpoint)
        form_layout.addRow("Model:", model_container)
        form_layout.addRow("API Key:", self.new_api_key)
        
        self.add_new_btn = QPushButton("Create && Add to Pool")
        self.add_new_btn.clicked.connect(self._add_new_to_pool)
        
        add_layout.addLayout(form_layout)
        add_layout.addWidget(self.add_new_btn)
        add_group.setLayout(add_layout)
        
        layout.addWidget(add_group)
        
        # --- Dialog Buttons ---
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        self.save_btn = QPushButton("Save Pool")
        self.save_btn.clicked.connect(self._save_pool)
        btn_layout.addWidget(self.save_btn)
        
        self.close_btn = QPushButton("Close")
        self.close_btn.clicked.connect(self.accept)
        btn_layout.addWidget(self.close_btn)
        
        layout.addLayout(btn_layout)

    def _refresh_pool_selector(self):
        self.pool_combo.blockSignals(True)
        self.pool_combo.clear()
        self.pool_combo.addItem("--- Select ---")
        self.pool_combo.addItems(list(self.pools.keys()))
        self.pool_combo.blockSignals(False)
        if self.pool_combo.count() > 1:
            self.pool_combo.setCurrentIndex(1)

    def _on_pool_changed(self, pool_name):
        self.api_list.clear()
        if pool_name and pool_name != "--- Select ---" and pool_name in self.pools:
            for api_name in self.pools[pool_name]:
                self.api_list.addItem(api_name)

    def _move_item(self, offset):
        current_row = self.api_list.currentRow()
        if current_row < 0: return
        new_row = current_row + offset
        if 0 <= new_row < self.api_list.count():
            item = self.api_list.takeItem(current_row)
            self.api_list.insertItem(new_row, item)
            self.api_list.setCurrentRow(new_row)

    def _remove_from_pool(self):
        current_row = self.api_list.currentRow()
        if current_row >= 0:
            self.api_list.takeItem(current_row)

    def _add_existing_to_pool(self):
        api_name = self.existing_api_combo.currentText()
        if api_name:
            self.api_list.addItem(api_name)

    def _add_new_to_pool(self):
        name = self.new_api_name.text().strip()
        if not name:
            QMessageBox.warning(self, "Error", "API Name cannot be empty.")
            return
            
        if name in self.api_profiles:
            QMessageBox.warning(self, "Error", f"API Profile '{name}' already exists.")
            return
            
        from app.core.api_utils import infer_ai_provider
        endpoint = self.new_api_endpoint.text().strip()
        provider = infer_ai_provider(endpoint)
        
        profile = {
            "type": "Standalone",
            "provider": provider,
            "endpoint": endpoint,
            "model": self.new_api_model.currentText().strip(),
            "key": self.new_api_key.text().strip()
        }
        
        self.api_profiles[name] = profile
        self.main_window._save_api_profiles(self.api_profiles)
        
        # Update existing combo
        self.existing_api_combo.addItem(name)
        
        # Add to list
        self.api_list.addItem(name)
        
        # Clear fields
        self.new_api_name.clear()
        self.new_api_endpoint.clear()
        self.new_api_model.clear()
        self.new_api_model.addItem("Auto")
        self.new_api_model.setCurrentText("Auto")
        self.new_api_key.clear()
        
        QMessageBox.information(self, "Success", f"New API Profile '{name}' created and added to the pool.")

    def _save_pool(self):
        pool_name = self.pool_combo.currentText().strip()
        if not pool_name or pool_name == "--- Select ---":
            QMessageBox.warning(self, "Error", "Please select a valid pool to save.")
            return
            
        apis = []
        for i in range(self.api_list.count()):
            apis.append(self.api_list.item(i).text())
            
        self.pools[pool_name] = apis
        self.main_window._save_pool_profiles(self.pools)
        
        self._refresh_pool_selector()
        self.pool_combo.setCurrentText(pool_name)
        QMessageBox.information(self, "Success", f"Pool '{pool_name}' saved.")

    def _create_new_pool(self):
        import PySide6.QtWidgets as QtWidgets
        name, ok = QtWidgets.QInputDialog.getText(self, "New Pool", "Enter new Pool Name:")
        if ok and name.strip():
            name = name.strip()
            if name in self.pools:
                QMessageBox.warning(self, "Error", f"Pool '{name}' already exists.")
                return
            self.pools[name] = []
            self.main_window._save_pool_profiles(self.pools)
            self._refresh_pool_selector()
            self.pool_combo.setCurrentText(name)

    def _delete_pool(self):
        pool_name = self.pool_combo.currentText().strip()
        if pool_name and pool_name != "--- Select ---" and pool_name in self.pools:
            reply = QMessageBox.question(self, "Confirm Delete", f"Are you sure you want to delete pool '{pool_name}'?",
                                         QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                         QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                del self.pools[pool_name]
                self.main_window._save_pool_profiles(self.pools)
                self._refresh_pool_selector()
                self.api_list.clear()

    def _fetch_models(self):
        endpoint = self.new_api_endpoint.text().strip()
        key = self.new_api_key.text().strip()
        from app.core.api_utils import infer_ai_provider
        ai_provider = infer_ai_provider(endpoint)
        
        if not endpoint:
            QMessageBox.warning(self, "Warning", "Please enter a valid URL in Endpoint URL.")
            return

        self.fetch_models_btn.setEnabled(False)
        self.fetch_models_btn.setText("...")

        def thread_target():
            from app.core.api_utils import fetch_remote_ai_models
            try:
                models = fetch_remote_ai_models(endpoint, key, ai_provider)
                self.models_fetched_signal.emit(models)
            except Exception as e:
                print(f"[ERROR] Failed to fetch models: {e}")
                self.models_fetched_signal.emit([])
            finally:
                self.fetch_finished_signal.emit()

        threading.Thread(target=thread_target, daemon=True).start()

    def _show_fetched_models(self, models):
        if not models:
            QMessageBox.warning(self, "Warning", "Failed to fetch models or no models found.")
            return
            
        current_text = self.new_api_model.currentText()
        self.new_api_model.blockSignals(True)
        self.new_api_model.clear()
        self.new_api_model.addItem("Auto")
        self.new_api_model.addItems(models)
        
        if current_text and (current_text in models or current_text == "Auto"):
            self.new_api_model.setCurrentText(current_text)
        else:
            self.new_api_model.setCurrentText("Auto")
        self.new_api_model.blockSignals(False)

    def _on_fetch_finished(self):
        self.fetch_models_btn.setEnabled(True)
        self.fetch_models_btn.setText("Fetch")

if __name__ == "__main__":
    import sys
    import os
    from PySide6.QtWidgets import QApplication
    # Add the project root to sys.path so 'desktop_ui' module can be found
    project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    
    app = QApplication(sys.argv)
    # Mock main_window for testing standalone
    class MockMainWindow:
        def _load_pool_profiles(self): return {}
        def _load_api_profiles(self): return {}
        def _save_pool_profiles(self, p): pass
        def _save_api_profiles(self, p): pass
    
    dialog = ManagePoolsDialog(MockMainWindow())
    dialog.exec()
