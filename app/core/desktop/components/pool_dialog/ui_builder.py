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
from app.core.desktop.components.ui_utils import natural_sort_key

def build_ui(dialog):
    def _(key, default):
        if dialog.parent() and hasattr(dialog.parent(), 'get_string'):
            val = dialog.parent().get_string(key)
            return val if val != key else default
        return default

    def set_lang(w, key, ltype="ui"):
        w.setProperty("lang_id", key)
        w.setProperty("lang_type", ltype)

    layout = QVBoxLayout(dialog)
    
    # --- Top: Pool Selection / Creation ---
    pool_sel_layout = QHBoxLayout()
    lbl_select_pool = QLabel(_("ui_select_pool", "Select Pool:"))
    set_lang(lbl_select_pool, "ui_select_pool")
    pool_sel_layout.addWidget(lbl_select_pool)
    
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
    lbl_apis_pool = QLabel(_("ui_apis_in_pool", "APIs in Pool (Ordered by Priority):"))
    set_lang(lbl_apis_pool, "ui_apis_in_pool")
    layout.addWidget(lbl_apis_pool)
    layout.addWidget(dialog.api_list)
    
    list_controls_layout = QHBoxLayout()
    dialog.up_btn = QPushButton(_("ui_btn_move_up", "Move Up"))
    set_lang(dialog.up_btn, "ui_btn_move_up")
    dialog.up_btn.clicked.connect(lambda: dialog._move_item(-1))
    
    dialog.down_btn = QPushButton(_("ui_btn_move_down", "Move Down"))
    set_lang(dialog.down_btn, "ui_btn_move_down")
    dialog.down_btn.clicked.connect(lambda: dialog._move_item(1))
    
    dialog.remove_api_btn = QPushButton(_("ui_btn_remove_from_pool", "Remove from Pool"))
    set_lang(dialog.remove_api_btn, "ui_btn_remove_from_pool")
    dialog.remove_api_btn.clicked.connect(dialog._remove_from_pool)
    
    list_controls_layout.addWidget(dialog.up_btn)
    list_controls_layout.addWidget(dialog.down_btn)
    list_controls_layout.addStretch()
    list_controls_layout.addWidget(dialog.remove_api_btn)
    layout.addLayout(list_controls_layout)
    
    # --- Bottom: Add API to Pool ---
    add_group = QGroupBox(_("ui_add_api_to_pool", "Add API to Pool"))
    set_lang(add_group, "ui_add_api_to_pool")
    add_layout = QVBoxLayout()
    
    # Existing API
    existing_layout = QHBoxLayout()
    lbl_add_existing = QLabel(_("ui_add_existing_api", "Add Existing API:"))
    set_lang(lbl_add_existing, "ui_add_existing_api")
    existing_layout.addWidget(lbl_add_existing)
    
    dialog.existing_api_combo = QComboBox()
    dialog.existing_api_combo.addItems(sorted(list(dialog.api_profiles.keys()), key=natural_sort_key))
    existing_layout.addWidget(dialog.existing_api_combo, stretch=1)
    
    dialog.add_existing_btn = QPushButton(_("ui_btn_add", "Add"))
    set_lang(dialog.add_existing_btn, "ui_btn_add")
    dialog.add_existing_btn.clicked.connect(dialog._add_existing_to_pool)
    existing_layout.addWidget(dialog.add_existing_btn)
    add_layout.addLayout(existing_layout)
    
    lbl_or_add_new = QLabel(_("ui_or_add_new_api", "--- OR Add New API ---"), alignment=Qt.AlignmentFlag.AlignCenter)
    set_lang(lbl_or_add_new, "ui_or_add_new_api")
    add_layout.addWidget(lbl_or_add_new)
    
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
    
    dialog.fetch_models_btn = QPushButton(_("ui_btn_fetch", "Fetch"))
    set_lang(dialog.fetch_models_btn, "ui_btn_fetch")
    dialog.fetch_models_btn.setFixedWidth(50)
    dialog.fetch_models_btn.setToolTip("Fetch Models")
    dialog.fetch_models_btn.clicked.connect(dialog._fetch_models)
    model_layout.addWidget(dialog.fetch_models_btn)
    
    model_container = QWidget()
    model_container.setLayout(model_layout)
    
    dialog.new_api_key = QLineEdit()
    dialog.new_api_key.setEchoMode(QLineEdit.EchoMode.Password)
    
    lbl_api_name = QLabel(_("ui_api_name", "API Name:"))
    set_lang(lbl_api_name, "ui_api_name")
    form_layout.addRow(lbl_api_name, dialog.new_api_name)
    
    lbl_endpoint = QLabel(_("ui_endpoint_url", "Endpoint URL:"))
    set_lang(lbl_endpoint, "ui_endpoint_url")
    form_layout.addRow(lbl_endpoint, dialog.new_api_endpoint)
    
    lbl_model = QLabel(_("ui_model", "Model:"))
    set_lang(lbl_model, "ui_model")
    form_layout.addRow(lbl_model, model_container)
    
    lbl_api_key = QLabel(_("ui_api_key", "API Key:"))
    set_lang(lbl_api_key, "ui_api_key")
    form_layout.addRow(lbl_api_key, dialog.new_api_key)
    
    dialog.add_new_btn = QPushButton(_("ui_btn_create_add_pool", "Create && Add to Pool"))
    set_lang(dialog.add_new_btn, "ui_btn_create_add_pool")
    dialog.add_new_btn.clicked.connect(dialog._add_new_to_pool)
    
    add_layout.addLayout(form_layout)
    add_layout.addWidget(dialog.add_new_btn)
    add_group.setLayout(add_layout)
    
    layout.addWidget(add_group)
    
    # --- Dialog Buttons ---
    btn_layout = QHBoxLayout()
    btn_layout.addStretch()
    
    dialog.save_btn = QPushButton(_("ui_btn_save_pool", "Save Pool"))
    set_lang(dialog.save_btn, "ui_btn_save_pool")
    dialog.save_btn.clicked.connect(dialog._save_pool)
    btn_layout.addWidget(dialog.save_btn)
    
    dialog.close_btn = QPushButton(_("ui_btn_close", "Close"))
    set_lang(dialog.close_btn, "ui_btn_close")
    dialog.close_btn.clicked.connect(dialog.accept)
    btn_layout.addWidget(dialog.close_btn)
    
    layout.addLayout(btn_layout)
