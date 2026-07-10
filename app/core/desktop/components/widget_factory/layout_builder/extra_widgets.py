"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.layout_builder.extra_widgets
- RESPONSIBILITY: Build additional setting widgets (font scale, theme manager).
- CALLED BY: app.core.desktop.components.widget_factory.layout_builder.__init__ (as Mixin)
- CALLS TO: app.core.desktop.components.widgets_helper.SearchableComboBox
- IN = OUT: Returns QWidget rows for extra configuration.
=============================================================================
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QVBoxLayout, QFrame, QLabel

from app.core.desktop.components.widgets_helper import SearchableComboBox

class ExtraWidgetsBuilderMixin:
    def create_font_scale_widget(self) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        label = QLabel("UI Font Scale:")
        label.setToolTip("Changes the font size for the entire application UI.")
        row_layout.addWidget(label, stretch=1)

        self.mw.font_scale_combobox = SearchableComboBox()
        self.mw.font_scale_combobox.addItems(["75%", "85%", "100% (Default)", "115%", "125%", "150%"])
        self.mw.font_scale_combobox.setCurrentText("100% (Default)")

        self.mw.font_scale_combobox.currentTextChanged.connect(self.mw._on_font_scale_changed)

        row_layout.addWidget(self.mw.font_scale_combobox, stretch=2)
        return row_widget

    def create_theme_manager_widget(self) -> QWidget:
        theme_frame = QFrame()
        theme_layout = QVBoxLayout(theme_frame)
        theme_layout.setContentsMargins(0, 10, 0, 0)

        label = QLabel("Appearance & Theme")
        font = label.font()
        font.setBold(True)
        label.setFont(font)
        theme_layout.addWidget(label)

        controls_frame = QWidget()
        controls_layout = QHBoxLayout(controls_frame)
        controls_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel("Select Theme ⚠⚠⚠")
        label.setToolTip(
            "Note:\n"
            "Selected button colors\n"
            "might not be styled correctly\n"
            "when using themes.\n"
            "Default: Default Qt"
        )
        controls_layout.addWidget(label)

        self.mw.theme_combobox = SearchableComboBox()
        self.mw.theme_combobox.setToolTip("Changes the visual appearance of the application. Default: Default Qt")
        self.mw._load_themes()
        self.mw.theme_combobox.setCurrentText("Default Qt")
        self.mw.theme_combobox.currentTextChanged.connect(self.mw._apply_theme)

        controls_layout.addWidget(self.mw.theme_combobox, stretch=1)
        theme_layout.addWidget(controls_frame)

        return theme_frame
