"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.layout_builder.dynamic_buttons
- RESPONSIBILITY: Setup and manage dynamic buttons next to widget fields.
- CALLED BY: app.core.desktop.components.widget_factory.layout_builder.__init__ (as Mixin)
- CALLS TO: QColorDialog, PySide6.QtWidgets
- IN = OUT: Adds dynamic action buttons to layouts and routes their events.
=============================================================================
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton, QColorDialog, QLineEdit
from PySide6.QtCore import QTimer
from typing import Any

class DynamicButtonsBuilderMixin:
    mw: Any

    def setup_dynamic_action_buttons(self, key: str, combo_box, right_layout):
        btn_container = QWidget()
        btn_layout = QHBoxLayout(btn_container)
        btn_layout.setContentsMargins(0, 0, 0, 0)
        btn_layout.setSpacing(2)

        btn_tick = QPushButton("✔️")
        btn_tick.setFixedSize(30, 30)
        btn_tick.setStyleSheet("color: #2ECC71; font-weight: bold;")
        
        btn_download = QPushButton("📥")
        btn_download.setFixedSize(30, 30)
        
        btn_search = QPushButton("🔍")
        btn_search.setFixedSize(30, 30)
        
        btn_delete = QPushButton("❌")
        btn_delete.setFixedSize(30, 30)
        btn_delete.setStyleSheet("color: #E74C3C;")
        
        btn_layout.addWidget(btn_tick)
        btn_layout.addWidget(btn_download)
        btn_layout.addWidget(btn_search)
        btn_layout.addWidget(btn_delete)
        
        right_layout.addWidget(btn_container)
        
        if not hasattr(self.mw, '_dynamic_btns_map'):
            self.mw._dynamic_btns_map = {}
            
        self.mw._dynamic_btns_map[key] = {
            'tick': btn_tick,
            'download': btn_download,
            'search': btn_search,
            'delete': btn_delete,
            'combo': combo_box
        }
        
        btn_tick.clicked.connect(lambda checked=False, k=key: self.mw._on_dynamic_btn_clicked(k, 'tick'))
        btn_download.clicked.connect(lambda checked=False, k=key: self.mw._on_dynamic_btn_clicked(k, 'download'))
        btn_search.clicked.connect(lambda checked=False, k=key: self.mw._on_dynamic_btn_clicked(k, 'search'))
        btn_delete.clicked.connect(lambda checked=False, k=key: self.mw._on_dynamic_btn_clicked(k, 'delete'))
        
        combo_box.currentIndexChanged.connect(lambda idx, k=key: self.mw._update_dynamic_btns(k))
        QTimer.singleShot(0, lambda k=key: self.mw._update_dynamic_btns(k))

    def handle_widget_button_click(self, key: str, associated_widget: QLineEdit):
        if key in ["font_color", "outline_color"]:
            current_color = associated_widget.text()
            if not current_color: current_color = "000000" if key == "font_color" else "FFFFFF"
            title = "Choose Font Color" if key == "font_color" else "Choose Outline Color"
            color = QColorDialog.getColor(initial=f"#{current_color}", title=title)
            if color.isValid():
                new_color_hex = color.name()[1:]
                associated_widget.setText(new_color_hex)
                self.mw._on_setting_changed(key)
