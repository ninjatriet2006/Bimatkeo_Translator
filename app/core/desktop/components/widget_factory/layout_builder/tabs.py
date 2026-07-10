"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.layout_builder.tabs
- RESPONSIBILITY: Build and populate the dynamic settings tabs.
- CALLED BY: app.core.desktop.components.widget_factory.layout_builder.__init__ (as Mixin)
- CALLS TO: app.core.desktop.components.ui_utils.build_grouped_settings_tabs
- IN = OUT: Injects tab building logic into LayoutBuilderFactory.
=============================================================================
"""
from PySide6.QtWidgets import QWidget, QVBoxLayout, QScrollArea, QFrame, QLabel

from app.core.desktop.components.ui_utils import build_grouped_settings_tabs

class TabsBuilderMixin:
    def build_dynamic_tab_content(self, tab_name: str, settings_list: list) -> QWidget:
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        raw_tab_name = tab_name
        if hasattr(self.mw, 'config_loader') and hasattr(self.mw.config_loader, 'get_lang_data'):
            lang_data = self.mw.config_loader.get_lang_data(self.mw.config_loader.app_language)
            if lang_data:
                tab_translations = lang_data.get("tabs", {})
                for eng_tab, loc_tab in tab_translations.items():
                    if loc_tab == tab_name:
                        raw_tab_name = eng_tab
                        break

        standard_settings = []
        advanced_settings = []
        for info in settings_list:
            if info.get("section") == "advanced":
                advanced_settings.append(info)
            else:
                standard_settings.append(info)

        for info in standard_settings:
            widget_row = self.create_setting_row(info)
            layout.addWidget(widget_row)

        if advanced_settings:
            layout.addSpacing(15)

            separator_container = QWidget()
            separator_layout = QVBoxLayout(separator_container)
            separator_layout.setContentsMargins(0, 5, 0, 5)
            separator_layout.setSpacing(5)

            label = QLabel("<b>ADVANCED SETTINGS</b>")

            line = QFrame()
            line.setFrameShape(QFrame.Shape.HLine)
            line.setFrameShadow(QFrame.Shadow.Sunken)

            separator_layout.addWidget(label)
            separator_layout.addWidget(line)

            layout.addWidget(separator_container)

            for info in advanced_settings:
                widget_row = self.create_setting_row(info)
                layout.addWidget(widget_row)

        if raw_tab_name == "Extra Settings":
            font_scale_widget = self.create_font_scale_widget()
            theme_manager_widget = self.create_theme_manager_widget()
            layout.addWidget(font_scale_widget)
            layout.addWidget(theme_manager_widget)

        layout.addStretch()
        scroll_area.setWidget(content_widget)
        return scroll_area

    def rebuild_settings_tab(self):
        current_tab_idx = self.mw.settings_tab_view.currentIndex()
        self.mw.settings_tab_view.clear()
        
        self.mw.config_loader.apply_language(self.mw.current_settings.get('app_language', 'English'))
        self.mw.config_loader.full_config_data = self.mw.config_loader._build_full_config_data()
        
        self.populate_all_tabs()
        
        if current_tab_idx < self.mw.settings_tab_view.count():
            self.mw.settings_tab_view.setCurrentIndex(current_tab_idx)

    def populate_all_tabs(self):
        config_data = self.mw.config_loader.full_config_data
        tab_order = self.mw.config_loader.get_tab_order()
        
        grouped_settings = build_grouped_settings_tabs(config_data, tab_order)

        for tab_name in tab_order:
            settings_list = grouped_settings.get(tab_name, [])
            tab_content_widget = self.build_dynamic_tab_content(tab_name, settings_list)
            self.mw.settings_tab_view.addTab(tab_content_widget, tab_name)
