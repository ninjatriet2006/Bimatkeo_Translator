"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.basic_widgets
- RESPONSIBILITY: basic_widgets.py module logic.
- CALLED BY: Various
- CALLS TO: Various
- IN = OUT: Defines logic for app.core.desktop.components.widget_factory.basic_widgets.
=============================================================================
"""
import os
from PySide6.QtWidgets import (
    QWidget, QHBoxLayout, QLabel, QCheckBox, QSlider,
    QLineEdit, QSpinBox, QPushButton, QMessageBox
)
from PySide6.QtCore import Qt, QUrl
from PySide6.QtGui import QDesktopServices

class BasicWidgetFactory:
    def __init__(self, main_window):
        self.mw = main_window

    def create_checkbox(self, info: dict) -> QCheckBox:
        check_box = QCheckBox("")
        if info.get("default") is True:
            check_box.setChecked(True)
        return check_box

    def create_slider(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(10)

        slider = QSlider(Qt.Orientation.Horizontal)
        slider.setFocusPolicy(Qt.FocusPolicy.NoFocus)

        value_label = QLabel()
        value_label.setMinimumWidth(45)
        value_label.setAlignment(Qt.AlignmentFlag.AlignRight)

        options = info.get("options", {})
        from_val = options.get("from_", 0)
        to_val = options.get("to", 100)

        multiplier = info.get("value_multiplier", 1)
        internal_precision = 100

        slider.setMinimum(int(from_val * internal_precision))
        slider.setMaximum(int(to_val * internal_precision))

        def update_label(value):
            actual_value = (value / internal_precision) * multiplier
            value_format = info.get("value_format", "{:.0f}")

            if 'f' in value_format:
                display_value = float(actual_value)
            else:
                display_value = int(round(actual_value))

            if value_label:
                value_label.setText(value_format.format(display_value))

        setattr(slider, "update_label_func", update_label)
        slider.valueChanged.connect(update_label)

        default_value = info.get("default")
        initial_slider_value = 0
        if default_value is not None:
            try:
                initial_slider_value = int((float(default_value) / multiplier) * internal_precision)
            except (ValueError, TypeError):
                initial_slider_value = 0

        slider.setValue(initial_slider_value)
        update_label(initial_slider_value)

        layout.addWidget(slider)
        layout.addWidget(value_label)
        return container

    def create_spinbox(self, info: dict) -> QSpinBox:
        spinbox = QSpinBox()
        spinbox.setMinimum(info.get("min", 0))
        spinbox.setMaximum(info.get("max", 100))
        
        default_val = info.get("default")
        if default_val is not None:
            try:
                spinbox.setValue(int(default_val))
            except ValueError:
                pass
                
        return spinbox

    def create_entry(self, info: dict) -> QLineEdit:
        entry = QLineEdit()
        default_text = info.get("default", "")
        if default_text is not None:
            entry.setText(str(default_text))

        placeholder = info.get("placeholder", "")
        if placeholder:
            entry.setPlaceholderText(placeholder)

        return entry

    def create_entry_with_button(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        entry = QLineEdit()
        entry.setText(str(info.get("default", "")))
        layout.addWidget(entry)

        button = QPushButton(info.get("button_text", "..."))
        button.setFixedWidth(40)
        button.clicked.connect(lambda: self.mw._handle_widget_button_click(info['key'], entry))
        layout.addWidget(button)

        return container

    def create_open_yaml_button(self, info: dict) -> QPushButton:
        button = QPushButton("Open Configuration (YAML) 📂")
        button.setProperty("lang_id", "ui_btn_open_yaml")
        button.setProperty("lang_type", "ui")
        file_name = info.get("default") or "Ignored.yaml"
        
        def on_click():
            file_path = os.path.join(self.mw.project_base_dir, ".config", "configs", file_name)
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            else:
                QMessageBox.warning(self.mw, "File Not Found", f"Configuration file not found: {file_path}")
                
        button.clicked.connect(on_click)
        return button
