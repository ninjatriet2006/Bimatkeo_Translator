"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.pool_dialog.ui_builder
- RESPONSIBILITY: Build the PySide6 UI layout for ManagePoolsDialog.
- CALLED BY: app.core.desktop.components.pool_dialog.dialog
- CALLS TO: PySide6.QtWidgets, app.core.desktop.components.widgets_helper.SearchableComboBox
- IN = OUT: Injects widgets into the given QDialog instance.
=============================================================================
"""
from PySide6.QtWidgets import (QVBoxLayout, QHBoxLayout, QLabel, 
                               QLineEdit, QPushButton, QListWidget, QComboBox,
                               QGroupBox, QFormLayout, QWidget)
from PySide6.QtCore import Qt
from app.core.desktop.components.widgets_helper import SearchableComboBox

def build_ui(dialog):
    layout = QVBoxLayout(dialog)
    
    # --- Top: Pool Selection / Creation ---
    pool_sel_layout = QHBoxLayout()
    pool_sel_layout.addWidget(QLabel("Select Pool:"))
    dialog.pool_combo = SearchableComboBox()
    dialog.pool_combo.currentTextChanged.connect(dialog._on_pool_changed)
    pool_sel_layout.addWidget(dialog.pool_combo, stretch=1)
    
    dialog.add_pool_btn = QPushButton("+")
    dialog.add_pool_btn.setFixedWidth(30)
    dialog.add_pool_btn.setToolTip("Create a new pool")
    dialog.add_pool_btn.clicked.connect(dialog._create_new_pool)
    pool_sel_layout.addWidget(dialog.add_pool_btn)
    
    dialog.delete_pool_btn = QPushButton("-")
    dialog.delete_pool_btn.setFixedWidth(30)
    dialog.delete_pool_btn.setToolTip("Delete this pool")
    dialog.delete_pool_btn.clicked.connect(dialog._delete_pool)
    pool_sel_layout.addWidget(dialog.delete_pool_btn)
    
    layout.addLayout(pool_sel_layout)
    
    # --- Middle: API List for the current pool ---
    dialog.api_list = QListWidget()
    layout.addWidget(QLabel("APIs in Pool (Ordered by Priority):"))
    layout.addWidget(dialog.api_list)
    
    list_controls_layout = QHBoxLayout()
    dialog.up_btn = QPushButton("Move Up")
    dialog.up_btn.clicked.connect(lambda: dialog._move_item(-1))
    dialog.down_btn = QPushButton("Move Down")
    dialog.down_btn.clicked.connect(lambda: dialog._move_item(1))
    dialog.remove_api_btn = QPushButton("Remove from Pool")
    dialog.remove_api_btn.clicked.connect(dialog._remove_from_pool)
    
    list_controls_layout.addWidget(dialog.up_btn)
    list_controls_layout.addWidget(dialog.down_btn)
    list_controls_layout.addStretch()
    list_controls_layout.addWidget(dialog.remove_api_btn)
    layout.addLayout(list_controls_layout)
    
    # --- Bottom: Add API to Pool ---
    add_group = QGroupBox("Add API to Pool")
    add_layout = QVBoxLayout()
    
    # Existing API
    existing_layout = QHBoxLayout()
    existing_layout.addWidget(QLabel("Add Existing API:"))
    dialog.existing_api_combo = QComboBox()
    dialog.existing_api_combo.addItems(list(dialog.api_profiles.keys()))
    existing_layout.addWidget(dialog.existing_api_combo, stretch=1)
    
    dialog.add_existing_btn = QPushButton("Add")
    dialog.add_existing_btn.clicked.connect(dialog._add_existing_to_pool)
    existing_layout.addWidget(dialog.add_existing_btn)
    add_layout.addLayout(existing_layout)
    
    add_layout.addWidget(QLabel("--- OR Add New API ---", alignment=Qt.AlignmentFlag.AlignCenter))
    
    # New API
    form_layout = QFormLayout()
    dialog.new_api_name = QLineEdit()
    dialog.new_api_endpoint = QLineEdit()
    
    dialog.new_api_model = SearchableComboBox()
    dialog.new_api_model.setEditable(True)
    dialog.new_api_model.addItem("Auto")
    dialog.new_api_model.setCurrentText("Auto")
    
    model_layout = QHBoxLayout()
    model_layout.setContentsMargins(0,0,0,0)
    model_layout.addWidget(dialog.new_api_model, stretch=1)
    dialog.fetch_models_btn = QPushButton("Fetch")
    dialog.fetch_models_btn.setFixedWidth(50)
    dialog.fetch_models_btn.setToolTip("Fetch Models")
    dialog.fetch_models_btn.clicked.connect(dialog._fetch_models)
    model_layout.addWidget(dialog.fetch_models_btn)
    
    model_container = QWidget()
    model_container.setLayout(model_layout)
    
    dialog.new_api_key = QLineEdit()
    dialog.new_api_key.setEchoMode(QLineEdit.EchoMode.Password)
    
    form_layout.addRow("API Name:", dialog.new_api_name)
    form_layout.addRow("Endpoint URL:", dialog.new_api_endpoint)
    form_layout.addRow("Model:", model_container)
    form_layout.addRow("API Key:", dialog.new_api_key)
    
    dialog.add_new_btn = QPushButton("Create && Add to Pool")
    dialog.add_new_btn.clicked.connect(dialog._add_new_to_pool)
    
    add_layout.addLayout(form_layout)
    add_layout.addWidget(dialog.add_new_btn)
    add_group.setLayout(add_layout)
    
    layout.addWidget(add_group)
    
    # --- Dialog Buttons ---
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    dialog.save_btn = QPushButton("Save Pool")
    dialog.save_btn.clicked.connect(dialog._save_pool)
    btn_layout.addWidget(dialog.save_btn)
    
    dialog.close_btn = QPushButton("Close")
    dialog.close_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(dialog.close_btn)
    
    layout.addLayout(btn_layout)
