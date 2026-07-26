"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.layout_builder.rows
- RESPONSIBILITY: Build individual settings rows dynamically based on dict config.
- CALLED BY: app.core.desktop.components.widget_factory.layout_builder.__init__ (as Mixin)
- CALLS TO: specialized widgets, basic widgets, complex widgets, app.core.desktop.recommend
- IN = OUT: Takes config dict, returns QWidget representing a row.
=============================================================================
"""
from PySide6.QtWidgets import QWidget, QHBoxLayout, QLabel
from PySide6.QtCore import Qt

from typing import Any

class RowsBuilderMixin:
    mw: Any
    setup_dynamic_action_buttons: Any
    def create_setting_row(self, info: dict, context_key: str | None = None) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        widget_type = info.get("widget")

        if widget_type == "label":
            label_text = self.mw.get_ui_string("settings", info.get("key", ""), "label")
            if label_text == info.get("key", ""):
                label_text = info.get("label", "")
            widget = QLabel(label_text)
            widget.setProperty("lang_id", info.get("key", ""))
            
            if "style" in info:
                widget.setStyleSheet(info["style"])
            row_layout.addWidget(widget)
            if not context_key:
                self.mw.setting_widgets[info['key']] = widget
                self.mw.setting_rows[info['key']] = row_widget
            return row_widget

        if widget_type == "embedded_console":
            from PySide6.QtWidgets import QTextEdit
            console = QTextEdit()
            console.setReadOnly(True)
            console.setStyleSheet("background-color: #1e1e1e; color: #00ff00; font-family: monospace;")
            console.setMinimumHeight(150)
            
            # Connect the translator log signal to this console
            if hasattr(self.mw, 'translator_log_signal'):
                self.mw.translator_log_signal.connect(lambda level, msg: console.append(f"[{level}] {msg}"))
            else:
                self.mw.log_signal.connect(lambda level, msg: console.append(f"[{level}] {msg}"))
            
            row_layout.addWidget(console)
            
            if not context_key:
                self.mw.setting_widgets[info['key']] = console
                self.mw.setting_rows[info['key']] = row_widget
            return row_widget

        if widget_type == "translator_chain_builder":
            widget = self.mw.specialized_widgets.create_translator_chain_builder(info)
            row_layout.addWidget(widget)

            if context_key:
                self.mw.task_widgets[context_key][info['key']] = widget
                if not hasattr(self.mw, 'task_rows'):
                    self.mw.task_rows = {}
                if context_key not in self.mw.task_rows:
                    self.mw.task_rows[context_key] = {}
                self.mw.task_rows[context_key][info['key']] = row_widget
            else:
                self.mw.setting_widgets[info['key']] = widget
                self.mw.setting_rows[info['key']] = row_widget
                if not hasattr(self.mw, 'widget_references'): 
                    self.mw.widget_references = {}
                self.mw.widget_references[info['key']] = widget

            self.mw._connect_widget_signal(info['key'], widget, context_key)

        else:
            label_container = QWidget()
            label_layout = QHBoxLayout(label_container)
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(5)

            label_text = self.mw.get_ui_string("settings", info.get("key", ""), "label")
            if label_text == info.get("key", ""):
                label_text = info.get("label", info.get("key", "N/A"))
                
            main_label = QLabel(label_text)
            main_label.setProperty("lang_id", info.get("key", ""))
            label_layout.addWidget(main_label)

            tooltip_text = self.mw.get_ui_string("settings", info.get("key", ""), "tooltip")
            if tooltip_text == info.get("key", ""):
                tooltip_text = info.get("tooltip", "")
                
            if tooltip_text:
                tooltip_icon = QLabel("(?)")
                tooltip_icon.setStyleSheet("color: #40E0D0;")
                tooltip_icon.setCursor(Qt.CursorShape.PointingHandCursor)
                default_val = info.get('default', 'N/A')
                full_tooltip = f"<b>{label_text}</b><hr>{tooltip_text}<br><i>(Default: {default_val})</i>"
                tooltip_icon.setToolTip(full_tooltip)
                tooltip_icon.setProperty("tooltip_lang_id", info.get("key", ""))
                label_layout.addWidget(tooltip_icon)

            label_layout.addStretch()
            row_layout.addWidget(label_container, stretch=1)

            if widget_type == "segmented_button":
                widget = self.mw.complex_widgets.create_segmented_button(info)
            elif widget_type in ["optionmenu", "optionmenu_languages", "optionmenu_separators"]:
                widget = self.mw.complex_widgets.create_combobox(info)
            elif widget_type == "checkbox":
                widget = self.mw.basic_widgets.create_checkbox(info)
            elif widget_type == "slider":
                widget = self.mw.basic_widgets.create_slider(info)
            elif widget_type == "entry":
                widget = self.mw.basic_widgets.create_entry(info)
            elif widget_type == "spinbox":
                widget = self.mw.basic_widgets.create_spinbox(info)
            elif widget_type == "open_yaml_button":
                widget = self.mw.basic_widgets.create_open_yaml_button(info)
            elif widget_type == "combobox_fonts":
                widget = self.mw.specialized_widgets.create_font_combobox(info)
            elif widget_type == "entry_with_button":
                widget = self.mw.basic_widgets.create_entry_with_button(info)
            elif widget_type == "api_profile_selector":
                widget = self.mw.specialized_widgets.create_api_profile_selector(info)
            elif widget_type == "pool_profile_selector":
                widget = self.mw.specialized_widgets.create_pool_profile_selector(info)
            elif widget_type == "ai_model_selector":
                widget = self.mw.specialized_widgets.create_ai_model_selector(info)
            elif widget_type == "api_key_manager":
                widget = self.mw.specialized_widgets.create_api_manager_widget(info)
            elif widget_type == "grid_segmented_button":
                widget = self.mw.complex_widgets.create_grid_segmented_button(info)
            else:
                widget = QLabel(f"TODO: '{widget_type}'")
                widget.setStyleSheet("color: yellow;")

            right_container = QWidget()
            right_layout = QHBoxLayout(right_container)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(5)
            
            right_layout.addWidget(widget, stretch=1)

            if not context_key and info.get('key') in ['offline_translator', 'offline_detector', 'offline_ocr', 'api_ocr', 'inpainter', 'upscaler', 'colorizer', 'renderer', 'font_family', 'sd_base_model']:
                self.setup_dynamic_action_buttons(info.get('key'), widget, right_layout)
            elif widget_type not in ["combobox_fonts", "entry_with_button", "translator_chain_builder", "api_key_manager", "api_profile_selector", "pool_profile_selector", "ai_model_selector"]:
                if info.get('recommendation'):
                    try:
                        from app.core.desktop.logic.recommend import get_recommended_size
                        rec_size = get_recommended_size()
                        rec_label = QLabel(f"(Recommend: {rec_size})")
                        rec_label.setStyleSheet("color: #4CAF50; font-size: 11px; font-style: italic;")
                        right_layout.addWidget(rec_label)
                    except Exception:
                        pass
                else:
                    spacer = QWidget()
                    spacer.setFixedWidth(30)
                    right_layout.addWidget(spacer)

            row_layout.addWidget(right_container, stretch=2)

            if context_key:
                self.mw.task_widgets[context_key][info['key']] = widget
                if not hasattr(self.mw, 'task_rows'):
                    self.mw.task_rows = {}
                if context_key not in self.mw.task_rows:
                    self.mw.task_rows[context_key] = {}
                self.mw.task_rows[context_key][info['key']] = row_widget
                initial_value = self.mw.task_settings[context_key].get(info['key'])
            else:
                self.mw.setting_widgets[info['key']] = widget
                self.mw.setting_rows[info['key']] = row_widget
                initial_value = self.mw.current_settings.get(info['key'])

            self.mw._set_widget_value(info['key'], initial_value, widget)
            self.mw._connect_widget_signal(info['key'], widget, context_key)

        return row_widget
