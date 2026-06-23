# type: ignore
# ===============================================================
# WidgetBuildersMixin - UI Layout Widget Builders
#
# Author: User & Gemini Collaboration
# ===============================================================

import os
import json
from .ui_utils import build_grouped_settings_tabs
import sys
import copy
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea,
    QButtonGroup, QListWidget, QListWidgetItem, QComboBox, QCheckBox, QSlider,
    QLineEdit, QGridLayout, QColorDialog
)
from PySide6.QtCore import Qt, QTimer, QSize
from PySide6.QtGui import QColor, QFont
from desktop_ui.constants import *


from .widgets_helper import (
    SearchableComboBox, NoScrollComboBox, DynamicHeightListWidget, SearchableFontInstallDialog
)

class WidgetBuildersMixin:
    def _build_dynamic_tab_content(self, tab_name: str, settings_list: list) -> QWidget:
        """
        Creates a scrollable area and populates it with settings widgets,
        now with a dedicated, collapsible section for advanced settings.
        """
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(8)

        # Resolve English tab name to handle localization dynamically
        raw_tab_name = tab_name
        if hasattr(self, 'config_loader') and hasattr(self.config_loader, 'get_lang_data'):
            lang_data = self.config_loader.get_lang_data(self.config_loader.app_language)
            if lang_data:
                tab_translations = lang_data.get("tabs", {})
                for eng_tab, loc_tab in tab_translations.items():
                    if loc_tab == tab_name:
                        raw_tab_name = eng_tab
                        break

        # Split settings into standard and advanced groups first
        standard_settings = []
        advanced_settings = []
        for info in settings_list:
            if info.get("key") in ["ai_translator"]:
                continue
            if info.get("section") == "advanced":
                advanced_settings.append(info)
            else:
                standard_settings.append(info)

        # 1. Render all standard settings
        for info in standard_settings:
            widget_row = self._create_setting_row(info)
            layout.addWidget(widget_row)

        # 2. Render the '''Advanced Settings''' separator and section
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

            # 3. Render all advanced settings
            for info in advanced_settings:
                widget_row = self._create_setting_row(info)
                layout.addWidget(widget_row)


        # Special handling for Extra Settings tab (Theme manager, etc.)
        if raw_tab_name == "Extra Settings":
            vram_info_label = QLabel()
            vram_info_label.setWordWrap(True)
            vram_info_label.setStyleSheet("font-size: 9pt; color: #999;")

            if self.detected_vram_gb > 0:
                vram_text = f"Detected {self.detected_vram_gb:.2f} GB of VRAM. "
                if self.detected_vram_gb <= 6:
                    vram_text += "<b>Recommendation: '''Low VRAM''' mode.</b>"
                else:
                    vram_text += "<b>Recommendation: '''High VRAM''' mode.</b>"
            else:
                vram_text = "Could not detect GPU VRAM. '''Low VRAM''' mode is recommended for safety."

            vram_info_label.setText(vram_text)
            layout.addWidget(vram_info_label)

            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            layout.addWidget(separator)

            font_scale_widget = self._create_font_scale_widget()
            theme_manager_widget = self._create_theme_manager_widget()
            layout.addWidget(font_scale_widget)
            layout.addWidget(theme_manager_widget)

        layout.addStretch()  # Pushes all widgets to the top
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _build_tasks_tab_content(self) -> QWidget:
        """Creates the content for the '''Tasks''' tab with improved layout."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(15)

        # This widget is created manually and not from ui_map.json
        device_widget_container = QWidget()
        device_layout = QHBoxLayout(device_widget_container)
        device_layout.setContentsMargins(0, 0, 0, 0)
        device_layout.addWidget(QLabel("Task Processing Device:"))

        # We reuse the segmented button logic for consistency
        seg_button_container = QWidget()
        seg_button_layout = QHBoxLayout(seg_button_container)
        seg_button_layout.setContentsMargins(0, 0, 0, 0)
        seg_button_layout.setSpacing(0)

        button_group = QButtonGroup(seg_button_container)
        button_group.setExclusive(True)

        for val in ["CPU", "NVIDIA GPU"]:
            button = QPushButton(val)
            button.setCheckable(True)
            seg_button_layout.addWidget(button)
            button_group.addButton(button)
            if val == "CPU":  # Default to CPU
                button.setChecked(True)

        seg_button_container.setLayout(seg_button_layout)
        device_layout.addWidget(seg_button_container, stretch=1)

        # Store a reference to this new widget so we can read its value later
        self.tasks_processing_device_widget = seg_button_container

        layout.addWidget(device_widget_container)

        # Add a separator line
        separator = QFrame()
        separator.setFrameShape(QFrame.Shape.HLine)
        separator.setFrameShadow(QFrame.Shadow.Sunken)
        layout.addWidget(separator)

        tasks_config = self.config_loader.tasks_config
        if not tasks_config:
            layout.addWidget(QLabel("Could not load tasks.json or it is empty."))
            content_widget.setLayout(layout)
            scroll_area.setWidget(content_widget)
            return scroll_area

        if not hasattr(self, '''task_settings'''):
            self.task_settings = {}
            self.task_widgets = {}

        for task_key, task_info in tasks_config.items():
            task_frame = QFrame()
            task_frame.setObjectName("StyledPanel")
            task_frame.setFrameShape(QFrame.Shape.StyledPanel)
            task_layout = QVBoxLayout(task_frame)

            # --- Top Section: Title and Description ---
            title_label = QLabel(task_info.get("label", "Unnamed Task"))
            font = title_label.font()
            font.setPointSize(12)
            font.setBold(True)
            title_label.setFont(font)
            task_layout.addWidget(title_label)

            description_label = QLabel(task_info.get("description", ""))
            description_label.setWordWrap(True)
            task_layout.addWidget(description_label)

            separator = QFrame()
            separator.setFrameShape(QFrame.Shape.HLine)
            separator.setFrameShadow(QFrame.Shadow.Sunken)
            task_layout.addWidget(separator)

            # --- Middle Section: Dynamically created settings ---
            self.task_settings.setdefault(task_key, task_info.get("defaults", {}).copy())
            self.task_widgets.setdefault(task_key, {})

            settings_keys = task_info.get("settings_keys", [])
            for setting_key in settings_keys:
                widget_info = self.config_loader.full_config_data.get(setting_key)
                if widget_info:
                    widget_row = self._create_setting_row(widget_info, task_key)
                    task_layout.addWidget(widget_row)
                else:
                    task_layout.addWidget(QLabel(f"Warning: Definition for '''{setting_key}''' not found."))

            if hasattr(self, '_update_task_translator_visibility'):
                self._update_task_translator_visibility(task_key)

            task_layout.addStretch(1)  # Add stretch to push buttons to the bottom

            # --- Bottom Section: Action Buttons ---
            button_container = QWidget()
            button_layout = QHBoxLayout(button_container)
            button_layout.setContentsMargins(0, 0, 0, 0)

            reset_button = QPushButton("Reset to Defaults")
            reset_button.clicked.connect(lambda checked, tk=task_key: self._reset_task_settings(tk))

            # Define the button first, then set its text and connect the signal.
            run_button = QPushButton()
            run_button.setText(f"Assign {task_info.get('label', 'Task')}")
            run_button.clicked.connect(lambda checked, tk=task_key: self._assign_task_to_selection(tk))

            button_layout.addWidget(reset_button, alignment=Qt.AlignmentFlag.AlignLeft)
            button_layout.addStretch()  # Pushes the two buttons apart
            button_layout.addWidget(run_button, alignment=Qt.AlignmentFlag.AlignRight)

            task_layout.addWidget(button_container)
            layout.addWidget(task_frame)

        layout.addStretch(1)  # Pushes all task frames to the top
        content_widget.setLayout(layout)
        scroll_area.setWidget(content_widget)
        return scroll_area

    def _create_setting_row(self, info: dict, context_key: str = None) -> QWidget:
        """
        Creates a single row (Label + Tooltip Icon + Widget) for a setting.
        This function now handles the special '''translator_chain_builder''' case separately
        to prevent duplicate labels.
        """
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        widget_type = info.get("widget")

        # --- SPECIAL CASE: Non-interactive Label ---
        if widget_type == "label":
            widget = QLabel(info.get("label", ""))
            if "style" in info:
                widget.setStyleSheet(info["style"])
            row_layout.addWidget(widget)
            if not context_key:
                self.setting_widgets[info['key']] = widget
                self.setting_rows[info['key']] = row_widget
            return row_widget

        # --- PATH 1: For the special self-contained widget ---
        if widget_type == "translator_chain_builder":
            widget = self._create_translator_chain_builder(info)
            row_layout.addWidget(widget)

            if context_key:
                self.task_widgets[context_key][info['key']] = widget
                if not hasattr(self, 'task_rows'):
                    self.task_rows = {}
                if context_key not in self.task_rows:
                    self.task_rows[context_key] = {}
                self.task_rows[context_key][info['key']] = row_widget
            else:
                self.setting_widgets[info['key']] = widget
                self.setting_rows[info['key']] = row_widget
                if not hasattr(self, '''widget_references'''): self.widget_references = {}
                self.widget_references[info['key']] = widget

            self._connect_widget_signal(info['key'], widget, context_key)

        # --- PATH 2: For all other standard widgets ---
        else:
            label_container = QWidget()
            label_layout = QHBoxLayout(label_container)
            label_layout.setContentsMargins(0, 0, 0, 0)
            label_layout.setSpacing(5)

            label_text = info.get("label", info.get("key", "N/A"))
            main_label = QLabel(label_text)
            label_layout.addWidget(main_label)

            tooltip_text = info.get("tooltip")
            if tooltip_text:
                tooltip_icon = QLabel("(?)")
                tooltip_icon.setStyleSheet("color: #40E0D0;")
                tooltip_icon.setCursor(Qt.CursorShape.PointingHandCursor)
                default_val = info.get('default', '''N/A''')
                full_tooltip = f"<b>{label_text}</b><hr>{tooltip_text}<br><i>(Default: {default_val})</i>"
                tooltip_icon.setToolTip(full_tooltip)
                label_layout.addWidget(tooltip_icon)

            label_layout.addStretch()
            row_layout.addWidget(label_container, stretch=1)

            if widget_type == "segmented_button":
                widget = self._create_segmented_button(info)
            elif widget_type in ["optionmenu", "optionmenu_languages", "optionmenu_separators"]:
                widget = self._create_combobox(info)
            elif widget_type == "checkbox":
                widget = self._create_checkbox(info)
            elif widget_type == "slider":
                widget = self._create_slider(info)
            elif widget_type == "entry":
                widget = self._create_entry(info)
            elif widget_type == "open_yaml_button":
                widget = self._create_open_yaml_button(info)
            elif widget_type == "combobox_fonts":
                widget = self._create_font_combobox(info)
            elif widget_type == "entry_with_button":
                widget = self._create_entry_with_button(info)

            elif widget_type == "api_profile_selector":
                widget = self._create_api_profile_selector(info)
            elif widget_type == "pool_profile_selector":
                widget = self._create_pool_profile_selector(info)
            elif widget_type == "ai_model_selector":
                widget = self._create_ai_model_selector(info)
            elif widget_type == "api_key_manager":
                widget = self._create_api_manager_widget(info)
            elif widget_type == "grid_segmented_button":
                widget = self._create_grid_segmented_button(info)
            elif widget_type == "preset_manager":
                widget = self._create_preset_manager(info)
            else:
                widget = QLabel(f"TODO: '''{widget_type}'''")
                widget.setStyleSheet("color: yellow;")

            right_container = QWidget()
            right_layout = QHBoxLayout(right_container)
            right_layout.setContentsMargins(0, 0, 0, 0)
            right_layout.setSpacing(5)
            
            right_layout.addWidget(widget, stretch=1)

            if not context_key and info.get('key') in ['offline_translator', 'ai_translator', 'offline_detector', 'offline_ocr', 'api_ocr', 'inpainter', 'upscaler', 'colorizer', 'renderer', 'font_family']:
                self._setup_dynamic_action_buttons(info.get('key'), widget, right_layout)
            elif widget_type not in ["combobox_fonts", "entry_with_button", "translator_chain_builder", "preset_manager", "api_key_manager", "api_profile_selector", "pool_profile_selector", "ai_model_selector"]:
                spacer = QWidget()
                spacer.setFixedWidth(30)
                right_layout.addWidget(spacer)

            row_layout.addWidget(right_container, stretch=2)

            if context_key:
                self.task_widgets[context_key][info['key']] = widget
                if not hasattr(self, 'task_rows'):
                    self.task_rows = {}
                if context_key not in self.task_rows:
                    self.task_rows[context_key] = {}
                self.task_rows[context_key][info['key']] = row_widget
                initial_value = self.task_settings[context_key].get(info['key'])
            else:
                self.setting_widgets[info['key']] = widget
                self.setting_rows[info['key']] = row_widget
                initial_value = self.current_settings.get(info['key'])

            self._set_widget_value(info['key'], initial_value, widget)
            self._connect_widget_signal(info['key'], widget, context_key)

        return row_widget


    def _setup_dynamic_action_buttons(self, key: str, combo_box, right_layout):
        from PySide6.QtWidgets import QWidget, QHBoxLayout, QPushButton
        
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
        
        if not hasattr(self, '_dynamic_btns_map'):
            self._dynamic_btns_map = {}
            
        self._dynamic_btns_map[key] = {
            'tick': btn_tick,
            'download': btn_download,
            'search': btn_search,
            'delete': btn_delete,
            'combo': combo_box
        }
        
        btn_tick.clicked.connect(lambda checked=False, k=key: self._on_dynamic_btn_clicked(k, 'tick'))
        btn_download.clicked.connect(lambda checked=False, k=key: self._on_dynamic_btn_clicked(k, 'download'))
        btn_search.clicked.connect(lambda checked=False, k=key: self._on_dynamic_btn_clicked(k, 'search'))
        btn_delete.clicked.connect(lambda checked=False, k=key: self._on_dynamic_btn_clicked(k, 'delete'))
        
        combo_box.currentIndexChanged.connect(lambda idx, k=key: self._update_dynamic_btns(k))
        from PySide6.QtCore import QTimer
        QTimer.singleShot(0, lambda k=key: self._update_dynamic_btns(k))

    def _create_open_yaml_button(self, info: dict) -> QPushButton:
        """Creates a button that opens a specific YAML config file in the default system editor."""
        from PySide6.QtGui import QDesktopServices
        from PySide6.QtCore import QUrl
        
        button = QPushButton("Open Configuration (YAML) 📂")
        file_name = info.get("default") or "skip_languages.yaml"
        
        def on_click():
            file_path = os.path.join(self.project_base_dir, ".config", "configs", file_name)
            if os.path.exists(file_path):
                QDesktopServices.openUrl(QUrl.fromLocalFile(file_path))
            else:
                QMessageBox.warning(self, "File Not Found", f"Configuration file not found: {file_path}")
                
        button.clicked.connect(on_click)
        return button

    def _rebuild_settings_tab(self):
        """Rebuilds the settings tabs dynamically when the application language changes."""
        current_tab_idx = self.settings_tab_view.currentIndex()
        self.settings_tab_view.clear()
        
        # Load and localize settings
        self.config_loader.localize_ui_map(self.current_settings.get('app_language', 'English'))
        self.config_loader.full_config_data = self.config_loader._build_full_config_data()
        
        # Re-build tabs
        self._populate_all_tabs()
        
        # Restore index if valid
        if current_tab_idx < self.settings_tab_view.count():
            self.settings_tab_view.setCurrentIndex(current_tab_idx)

    def _populate_all_tabs(self):
        config_data = self.config_loader.full_config_data
        tab_order = self.config_loader.get_tab_order()
        
        grouped_settings = build_grouped_settings_tabs(config_data, tab_order)

        for tab_name in tab_order:
            settings_list = grouped_settings.get(tab_name, [])
            tab_content_widget = self._build_dynamic_tab_content(tab_name, settings_list)
            self.settings_tab_view.addTab(tab_content_widget, tab_name)

        tasks_tab_content = self._build_tasks_tab_content()
        self.settings_tab_view.addTab(tasks_tab_content, "Tasks 🛠️")

    def _create_segmented_button(self, info: dict) -> QWidget:
        """Creates a group of toggleable buttons."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        button_group = QButtonGroup(container)
        button_group.setExclusive(True)

        values = info.get("values", [])
        for val in values:
            button = QPushButton(val)
            button.setCheckable(True)
            if val == info.get("default"):
                button.setChecked(True)
            layout.addWidget(button)
            button_group.addButton(button)

        return container

    def _set_combobox_value_by_data(self, combo_box, value):
        index = -1
        for i in range(combo_box.count()):
            if combo_box.itemData(i) == value:
                index = i
                break
        if index != -1:
            combo_box.setCurrentIndex(index)
        else:
            combo_box.setCurrentText(str(value))

    def _create_combobox(self, info: dict) -> QComboBox:
        """Creates a dropdown (ComboBox) widget."""
        from .. import main_window as mw
        combo_box = SearchableComboBox()
        values = info.get("values", [])
        key = info.get("key")

        # Override values for UI-only translators if needed
        if key == "offline_translator":
            values = mw.TRANSLATOR_GROUPS.get(CAT_OFFLINE_MODELS, values)
        elif key == "ai_translator":
            values = mw.TRANSLATOR_GROUPS.get(CAT_API_BASED, values)

        if info.get("widget") == "optionmenu_languages":
            # Populate languages excluding Auto-Detect
            combo_box.addItem("--- Select ---", "none")
            for name, code in sorted(mw.LANGUAGES.items()):
                if code != "auto":
                    combo_box.addItem(name, code)
            self._set_combobox_value_by_data(combo_box, str(info.get("default")))
        elif info.get("widget") == "optionmenu_separators" or key in ["offline_translator", "ai_translator"]:
            # If it'''s the main translator selectors or has separators
            if key in ["offline_translator", "ai_translator"]:
                combo_box.addItem("--- Select ---", "none")
                info["default"] = "none"  # Force default to none for new users
                for val in values:
                    exists = self.config_loader.check_model_existence(val, field=key)
                    display_name = self.config_loader.format_display_label(val, key)
                    if not exists:
                        display_name = f"{display_name} (Not Setup)"
                    combo_box.addItem(display_name, val)
                    if not exists:
                        last_idx = combo_box.count() - 1
                        combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                is_en = self.current_settings.get('app_language', 'English') == 'English'
                update_support_text = UPDATE_SUPPORTED_LANGS_EN if is_en else UPDATE_SUPPORTED_LANGS
                update_all_text = UPDATE_ALL_MODELS_EN if is_en else UPDATE_ALL_MODELS
                combo_box.addItem(update_support_text, "update_trigger")
                combo_box.addItem(update_all_text, "update_all_software_trigger")
            else:
                # Optionmenu with separators (e.g. from TRANSLATOR_GROUPS)
                for group_name, translators in mw.TRANSLATOR_GROUPS.items():
                    item_index = combo_box.count()
                    combo_box.addItem(group_name)
                    combo_box.model().item(item_index).setEnabled(False)
                    field_name = "offline_translator" if "OFFLINE" in group_name else ("ai_translator" if "API" in group_name else None)
                    for t in translators:
                        exists = self.config_loader.check_model_existence(t, field=field_name)
                        display_name = self.config_loader.format_display_label(t, field_name)
                        if not exists:
                            display_name = f"{display_name} (Not Setup)"
                        combo_box.addItem(display_name, t)
                        if not exists:
                            last_idx = combo_box.count() - 1
                            combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            self._set_combobox_value_by_data(combo_box, str(info.get("default")))
        else:
            if key in ['offline_detector', 'offline_ocr', 'api_ocr', 'inpainter', 'upscaler', 'colorizer', 'renderer']:
                combo_box.addItem("--- Select ---", "none")
            for val in values:
                exists = self.config_loader.check_model_existence(val, field=key)
                display_name = self.config_loader.format_display_label(val, key)
                if not exists:
                    display_name = f"{display_name} (Not Setup)"
                combo_box.addItem(display_name, val)
                if not exists:
                    last_idx = combo_box.count() - 1
                    combo_box.setItemData(last_idx, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
            
            # Thêm lựa chọn cập nhật tất cả cho các mô hình AI khác
            if key in ['offline_detector', 'offline_ocr', 'api_ocr', 'inpainter', 'upscaler', 'colorizer', 'renderer']:
                is_en = self.current_settings.get('app_language', 'English') == 'English'
                update_all_key_text = f"📥 Update ALL {key} models..." if is_en else f"📥 Cập nhật TẤT CẢ mô hình {key}..."
                combo_box.addItem(update_all_key_text, "update_all_software_trigger")
                
            self._set_combobox_value_by_data(combo_box, str(info.get("default")))

        return combo_box

    def _create_checkbox(self, info: dict) -> QCheckBox:
        """Creates a checkbox widget."""
        check_box = QCheckBox("")
        if info.get("default") is True:
            check_box.setChecked(True)
        return check_box

    def _create_slider(self, info: dict) -> QWidget:
        """Creates a container with a QSlider and a QLabel to display its value."""
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

            if '''f''' in value_format:
                display_value = float(actual_value)
            else:
                display_value = int(round(actual_value))

            if value_label:
                value_label.setText(value_format.format(display_value))

        slider.update_label_func = update_label
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

    def _create_entry(self, info: dict) -> QLineEdit:
        """Creates a text input (QLineEdit) widget."""
        entry = QLineEdit()
        default_text = info.get("default", "")
        if default_text is not None:
            entry.setText(str(default_text))

        placeholder = info.get("placeholder", "")
        if placeholder:
            entry.setPlaceholderText(placeholder)

        return entry

    def _create_entry_with_button(self, info: dict) -> QWidget:
        """Creates a QLineEdit with a QPushButton next to it."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)

        entry = QLineEdit()
        entry.setText(str(info.get("default", "")))
        layout.addWidget(entry)

        button = QPushButton(info.get("button_text", "..."))
        button.setFixedWidth(40)
        button.clicked.connect(lambda: self._handle_widget_button_click(info['key'], entry))
        layout.addWidget(button)

        return container

    def _create_translator_chain_builder(self, info: dict) -> QWidget:
        """
        Creates a self-contained component for the translator chain,
        including its own header with a label and control buttons.
        """
        container = QFrame()
        container.setObjectName("ChainBuilderFrame")
        container_layout = QVBoxLayout(container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.setSpacing(5)

        # --- Header Row ---
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)

        label = QLabel(info.get("label", "Translation Steps:"))
        header_layout.addWidget(label)
        header_layout.addStretch()

        add_btn = QPushButton("➕ Add Step")
        remove_btn = QPushButton("➖ Remove Selected")
        header_layout.addWidget(add_btn)
        header_layout.addWidget(remove_btn)

        container_layout.addWidget(header_widget)

        # --- List Widget ---
        self.chain_list_widget = DynamicHeightListWidget()
        self.chain_list_widget.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        container_layout.addWidget(self.chain_list_widget)

        # --- Connect signals ---
        add_btn.clicked.connect(self._add_chain_step)
        remove_btn.clicked.connect(self._remove_chain_step)

        self.widget_references[info['key']] = container

        QTimer.singleShot(0, self._update_chain_ui_state)

        return container

    def _create_chain_step_widget(self) -> QWidget:
        """Creates the widget for a single row/step in the translator chain."""
        from .. import main_window as mw
        step_widget = QWidget()
        layout = QHBoxLayout(step_widget)
        layout.setContentsMargins(5, 5, 5, 5)

        lang_combo = NoScrollComboBox()
        lang_items = [name for name, code in mw.LANGUAGES.items() if code != '''auto''']
        lang_combo.addItems(sorted(lang_items))

        translator_combo = NoScrollComboBox()

        layout.addWidget(QLabel("Translate to:"))
        layout.addWidget(lang_combo)
        layout.addWidget(QLabel("with:"))
        layout.addWidget(translator_combo)

        step_widget.translator_combo = translator_combo
        step_widget.lang_combo = lang_combo

        lang_combo.currentTextChanged.connect(
            lambda text, tc=translator_combo: self._filter_chain_step_translator_dropdown(text, tc)
        )
        self._filter_chain_step_translator_dropdown(lang_combo.currentText(), translator_combo)

        handler = lambda: self._on_setting_changed('translator_chain')
        translator_combo.currentTextChanged.connect(handler)
        lang_combo.currentTextChanged.connect(handler)

        return step_widget

    def _add_chain_step(self):
        """Adds a new, empty step to the translator chain list."""
        step_widget = self._create_chain_step_widget()

        list_item = QListWidgetItem(self.chain_list_widget)
        list_item.setSizeHint(step_widget.sizeHint())

        self.chain_list_widget.addItem(list_item)
        self.chain_list_widget.setItemWidget(list_item, step_widget)
        self._on_setting_changed('translator_chain')
        self.chain_list_widget.updateGeometry()

    def _remove_chain_step(self):
        """Removes the currently selected step from the chain list."""
        selected_items = self.chain_list_widget.selectedItems()
        if not selected_items:
            return
        for item in selected_items:
            row = self.chain_list_widget.row(item)
            self.chain_list_widget.takeItem(row)
        self._on_setting_changed('translator_chain')
        self.chain_list_widget.updateGeometry()

    def _get_translator_chain_string(self) -> str:
        """
        Reads all steps from the chain_list_widget and builds the
        backend-compatible string (e.g., '''sugoi:ENG;deepl:TRK''').
        """
        from .. import main_window as mw
        if not hasattr(self, '''chain_list_widget'''):
            return ""

        steps = []
        for i in range(self.chain_list_widget.count()):
            item = self.chain_list_widget.item(i)
            widget = self.chain_list_widget.itemWidget(item)

            if widget and hasattr(widget, '''translator_combo''') and hasattr(widget, '''lang_combo'''):
                translator_name = widget.translator_combo.currentData()
                if not translator_name:
                    translator_name = widget.translator_combo.currentText()
                lang_name = widget.lang_combo.currentText()

                if translator_name not in mw.TRANSLATOR_GROUPS:
                    lang_code = mw.LANGUAGES.get(lang_name, '')
                    if lang_code:
                        steps.append(f"{translator_name}:{lang_code}")

        return ";".join(steps)

    def _rebuild_chain_from_string(self, chain_string: str):
        """Clears and rebuilds the translator chain UI from a saved string."""
        from .. import main_window as mw
        self.chain_list_widget.clear()
        if not chain_string:
            return

        steps = chain_string.split(';')
        code_to_lang_name = {v: k for k, v in mw.LANGUAGES.items()}

        for step in steps:
            parts = step.split(':')
            if len(parts) == 2:
                translator_name, lang_code = parts

                step_widget = self._create_chain_step_widget()
                list_item = QListWidgetItem(self.chain_list_widget)
                list_item.setSizeHint(step_widget.sizeHint())
                self.chain_list_widget.addItem(list_item)
                self.chain_list_widget.setItemWidget(list_item, step_widget)

                lang_name = code_to_lang_name.get(lang_code, "")
                if lang_name:
                    step_widget.lang_combo.setCurrentText(lang_name)
                self._set_combobox_value_by_data(step_widget.translator_combo, translator_name)

        self.chain_list_widget.updateGeometry()

    def _create_grid_segmented_button(self, info: dict) -> QWidget:
        """Creates a grid of toggleable buttons that can wrap to multiple lines."""
        container = QWidget()
        layout = QGridLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)

        button_group = QButtonGroup(container)
        button_group.setExclusive(True)

        values = info.get("values", [])
        columns = info.get("options", {}).get("columns", 4)

        row, col = 0, 0
        for val in values:
            button = QPushButton(val)
            button.setCheckable(True)
            if val == info.get("default"):
                button.setChecked(True)

            layout.addWidget(button, row, col)
            button_group.addButton(button)

            col += 1
            if col >= columns:
                col = 0
                row += 1

        return container

    def _create_preset_manager(self, info: dict) -> QWidget:
        """Creates the preset management compound widget."""
        preset_frame = QFrame()
        preset_frame.setObjectName("StyledPanel")
        preset_frame.setFrameShape(QFrame.Shape.StyledPanel)
        layout = QVBoxLayout(preset_frame)

        self.profile_combobox = SearchableComboBox()
        layout.addWidget(self.profile_combobox)

        self.profile_name_entry = QLineEdit()
        self.profile_name_entry.setPlaceholderText("Enter new preset name")
        layout.addWidget(self.profile_name_entry)

        self.profile_combobox.currentTextChanged.connect(self.profile_name_entry.setText)

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(0, 0, 0, 0)

        save_btn = QPushButton("Save")
        load_btn = QPushButton("Load")
        delete_btn = QPushButton("Delete")

        button_layout.addWidget(save_btn)
        button_layout.addWidget(load_btn)
        button_layout.addWidget(delete_btn)
        layout.addWidget(button_container)

        save_btn.clicked.connect(self._save_profile)
        load_btn.clicked.connect(self._load_profile)
        delete_btn.clicked.connect(self._delete_profile)

        self._refresh_profile_list()
        return preset_frame

    def _update_chain_ui_state(self):
        """
        Enables or disables the translator chain builder and the main translator dropdowns
        based on the '''Enable Translator Chain''' checkbox.
        """
        enable_checkbox = self.setting_widgets.get('enable_translator_chain')
        chain_container = self.widget_references.get('translator_chain')
        category_widget = self.setting_widgets.get('translator_category')
        offline_combo = self.setting_widgets.get('offline_translator')
        ai_combo = self.setting_widgets.get('ai_translator')
        ai_endpoint = self.setting_widgets.get('ai_endpoint')
        ai_model_widget = self.setting_widgets.get('ai_model')
        ai_key = self.setting_widgets.get('ai_key')
        main_language_combo = self.setting_widgets.get('target_lang')

        if not all([enable_checkbox, chain_container, main_language_combo]):
            return

        is_chain_enabled = enable_checkbox.isChecked()

        chain_container.setEnabled(is_chain_enabled)
        main_language_combo.setEnabled(not is_chain_enabled)
        
        for w in [category_widget, offline_combo, ai_combo, ai_endpoint, ai_model_widget, ai_key]:
            if w:
                w.setEnabled(not is_chain_enabled)

        if not is_chain_enabled:
            self._update_translator_visibility()

        if not is_chain_enabled:
            self.chain_list_widget.clear()
            self.chain_list_widget.updateGeometry()

        self._on_setting_changed('translator_chain')

    def _update_chain_list_height(self):
        """Calculates and sets the minimum height of the chain list widget to fit all its items."""
        if not hasattr(self, '''chain_list_widget'''):
            return

        content_height = 0
        for i in range(self.chain_list_widget.count()):
            content_height += self.chain_list_widget.sizeHintForRow(i)

        if self.chain_list_widget.count() > 1:
            content_height += self.chain_list_widget.spacing() * (self.chain_list_widget.count() - 1)

        if content_height == 0:
            content_height = 40

        self.chain_list_widget.setMinimumHeight(content_height)

    def _update_translator_tooltip(self, translator_name: str):
        """Updates the tooltip of the translator combobox to show its capabilities."""
        from .. import main_window as mw
        category = self._get_active_translator_category()
        key = '''offline_translator''' if category == '''Offline''' else '''ai_translator'''
        translator_combo = self.setting_widgets.get(key)
        if not translator_combo:
            return

        from app.core.factories import TranslatorFactory
        capabilities = TranslatorFactory.get_capabilities(translator_name)
        code_to_name = {v: k for k, v in mw.LANGUAGES.items()}

        label = self.config_loader.format_display_label(translator_name, key)
        header = label if label == translator_name else f"{label} ({translator_name})"
        tooltip_html = f"<b>{header} Capabilities:</b><hr>"

        if not capabilities:
            tooltip_html += "No translation is performed."
        elif capabilities.get('__any__') == '__all__':
            tooltip_html += "Supports translation between most languages."
        else:
            lines = []
            for source_code, target_codes in capabilities.items():
                source_name = code_to_name.get(source_code, source_code)
                target_names = [code_to_name.get(tc, tc) for tc in target_codes]
                lines.append(f"<b>From {source_name}:</b><br>  → {', '.join(target_names)}")
            tooltip_html += "<br>".join(lines)

        translator_combo.setToolTip(tooltip_html)

    def _handle_widget_button_click(self, key: str, associated_widget: QWidget):
        """Handles clicks for buttons that are part of a widget row."""
        if key == "font_color":
            current_color = associated_widget.text()
            if not current_color: current_color = "000000"
            color = QColorDialog.getColor(initial=f"#{current_color}", title="Choose Font Color")
            if color.isValid():
                new_color_hex = color.name()[1:]
                associated_widget.setText(new_color_hex)
                self._on_setting_changed(key)
        
        elif key == "ai_model":
            button = associated_widget.parent().findChild(QPushButton)
            if button:
                self._fetch_ai_models(button)

    def _create_api_profile_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        service = info.get("service", "Translator")
        
        combo = SearchableComboBox()
        profiles = self._load_api_profiles()
        
        filtered_profiles = [name for name, p in profiles.items() if p.get("type", p.get("group", "Standalone")) == "Standalone" and p.get("service", "Translator") == service]
            
        combo.addItem("--- Select ---")
        combo.addItems(filtered_profiles)
        
        default_val = self.current_settings.get(info['key'], info.get("default", ""))
        combo.setCurrentText(str(default_val) if default_val else "--- Select ---")
            
        layout.addWidget(combo, stretch=1)
        
        save_btn = QPushButton("+")
        save_btn.setFixedWidth(30)
        save_btn.setToolTip("Save this profile to local config")
        if service == "OCR":
            save_btn.clicked.connect(self._save_current_ocr_api_profile)
        else:
            save_btn.clicked.connect(self._save_current_api_profile)
        layout.addWidget(save_btn)
        
        del_btn = QPushButton("-")
        del_btn.setFixedWidth(30)
        del_btn.setToolTip("Delete this profile from local config")
        if service == "OCR":
            del_btn.clicked.connect(self._delete_current_ocr_api_profile)
        else:
            del_btn.clicked.connect(self._delete_current_api_profile)
        layout.addWidget(del_btn)
        
        self.widget_references[info['key']] = combo
        return container

    def _create_pool_profile_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        service = info.get("service", "Translator")
        
        combo = SearchableComboBox()
        pools = self._load_pool_profiles(service)
        filtered_pools = list(pools.keys())
            
        combo.addItem("--- Select ---")
        combo.addItems(filtered_pools)
        
        default_val = self.current_settings.get(info['key'], info.get("default", ""))
        combo.setCurrentText(str(default_val) if default_val else "--- Select ---")
            
        layout.addWidget(combo, stretch=1)
        
        manage_btn = QPushButton("Manage Pools")
        manage_btn.setToolTip("Open Manage Pools Dialog")
        manage_btn.clicked.connect(lambda _, s=service: self._open_manage_pools_dialog(s))
        layout.addWidget(manage_btn)
        
        self.widget_references[info['key']] = combo
        return container

    def _create_ai_model_selector(self, info: dict) -> QWidget:
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(5)
        
        combo = SearchableComboBox()
        combo.setEditable(True)
        
        combo.addItem("Auto")
        
        default_val = info.get("default", "")
        if default_val and default_val != "Auto":
            combo.addItem(str(default_val))
            combo.setCurrentText(str(default_val))
        else:
            combo.setCurrentText("Auto")
            
        layout.addWidget(combo, stretch=1)
        
        fetch_btn = QPushButton(info.get("button_text", "Fetch"))
        fetch_btn.setFixedWidth(50)
        fetch_btn.clicked.connect(lambda: self._fetch_ai_models(fetch_btn))
        layout.addWidget(fetch_btn)
        
        self.widget_references[info['key']] = combo
        return container

    def _create_bottom_panel(self) -> QWidget:
        """Creates the bottom panel with progress bar and control buttons."""
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.Shape.NoFrame)
        layout = QHBoxLayout(bottom_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(5, 5, 5, 5)

        self.progress_label = QLabel("Ready")
        self.progress_label.setMinimumWidth(200)

        # To avoid errors, since self.progress_bar will be created in central widget setup,
        # we just create it normally here.
        from PySide6.QtWidgets import QProgressBar
        self.progress_bar = QProgressBar()
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        self.progress_bar.setFormat("%p% - %v/%m pages")

        progress_layout.addWidget(self.progress_label)
        progress_layout.addWidget(self.progress_bar, stretch=1)

        self.start_button = QPushButton("▶️ START")
        self.start_button.clicked.connect(self._start_pipeline_thread)
        self.start_button.setFixedHeight(40)
        font = self.start_button.font()
        font.setBold(True)
        self.start_button.setFont(font)

        self.stop_button = QPushButton("⏹️ STOP")
        self.stop_button.clicked.connect(self._stop_pipeline)
        self.stop_button.setEnabled(False)
        self.stop_button.setFixedHeight(40)
        stop_font = self.stop_button.font()
        stop_font.setBold(True)
        self.stop_button.setFont(stop_font)

        layout.addWidget(progress_widget, stretch=1)
        layout.addWidget(self.start_button)
        layout.addWidget(self.stop_button)

        return bottom_frame

    def _create_font_scale_widget(self) -> QWidget:
        """Creates a special row for the UI font scaling option."""
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        label = QLabel("UI Font Scale:")
        label.setToolTip("Changes the font size for the entire application UI.")
        row_layout.addWidget(label, stretch=1)

        self.font_scale_combobox = SearchableComboBox()
        self.font_scale_combobox.addItems(["75%", "85%", "100% (Default)", "115%", "125%", "150%"])
        self.font_scale_combobox.setCurrentText("100% (Default)")

        self.font_scale_combobox.currentTextChanged.connect(self._on_font_scale_changed)

        row_layout.addWidget(self.font_scale_combobox, stretch=2)
        return row_widget

    def _create_theme_manager_widget(self) -> QWidget:
        """Creates the UI component for theme selection."""
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

        self.theme_combobox = SearchableComboBox()
        self.theme_combobox.setToolTip("Changes the visual appearance of the application. Default: Default Qt")
        self._load_themes()
        self.theme_combobox.setCurrentText("Default Qt")
        self.theme_combobox.currentTextChanged.connect(self._apply_theme)

        controls_layout.addWidget(self.theme_combobox, stretch=1)
        theme_layout.addWidget(controls_frame)

        return theme_frame

    def _create_api_manager_widget(self, info: dict) -> QWidget:
        """Returns an empty widget since keys.yaml is deprecated."""
        return QWidget()

    def _create_font_combobox(self, info: dict) -> QWidget:
        """Creates a SearchableComboBox for fonts."""
        combo_box = SearchableComboBox()
        font_names = list(self.font_map.keys())
        
        default_font = info.get("default", "Sans-serif")
        if not default_font:
            default_font = "Sans-serif"

        if default_font not in font_names:
            font_names.insert(0, default_font)

        for font in font_names:
            is_google = self._get_google_font_family_from_filename(font) is not None
            display_text = font if is_google else f"{font} (Unavailable in fonts stores)"
            combo_box.addItem(display_text, userData=font)
        combo_box.addItem(INSTALL_NEW_FONT)
        combo_box.addItem(UPDATE_ALL_FONTS)

        # Set current index using data
        idx = combo_box.findData(default_font)
        if idx != -1:
            combo_box.setCurrentIndex(idx)
        else:
            combo_box.setCurrentText(default_font)
            
        self._last_selected_font = default_font

        self._style_custom_fonts_in_combobox(combo_box)

        def on_combo_text_changed(text):
            if text not in [INSTALL_NEW_FONT, UPDATE_ALL_FONTS]:
                actual_font = combo_box.currentData()
                if actual_font is None:
                    actual_font = text
                self._last_selected_font = actual_font
                is_google = self._get_google_font_family_from_filename(actual_font) is not None
                
                is_warning = not is_google
                combo_box.setProperty("warning", "true" if is_warning else "false")
                combo_box.style().unpolish(combo_box)
                combo_box.style().polish(combo_box)
                
                self._on_setting_changed('font_family')

        combo_box.currentTextChanged.connect(on_combo_text_changed)
        return combo_box

    def _style_custom_fonts_in_combobox(self, combo_box: QComboBox):
        """Styles custom (non-Google) fonts in the combobox items with yellow/amber foreground color."""
        for i in range(combo_box.count()):
            text = combo_box.itemText(i)
            if text not in [INSTALL_NEW_FONT, UPDATE_ALL_FONTS]:
                actual_font = combo_box.itemData(i)
                if actual_font is None:
                    actual_font = text
                is_google = self._get_google_font_family_from_filename(actual_font) is not None
                if not is_google:
                    combo_box.setItemData(i, QColor("#888888"), Qt.ItemDataRole.ForegroundRole)
                    
        curr_text = combo_box.currentText()
        actual_curr_font = combo_box.currentData()
        if actual_curr_font is None:
            actual_curr_font = curr_text
        is_google_curr = self._get_google_font_family_from_filename(actual_curr_font) is not None
        is_warn = not is_google_curr and curr_text not in [INSTALL_NEW_FONT, UPDATE_ALL_FONTS]
        combo_box.setProperty("warning", "true" if is_warn else "false")
        combo_box.style().unpolish(combo_box)
        combo_box.style().polish(combo_box)

    def _get_themed_arrow_icon_path(self, color_hex: str, theme_name: str) -> str:
        """Generates a themed down-arrow PNG icon and returns its absolute path."""
        base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        temp_dir = os.path.join(base_dir, "temp")
        os.makedirs(temp_dir, exist_ok=True)
        
        img_path = os.path.join(temp_dir, f"arrow_{theme_name.replace(' ', '_')}.png")
        if os.path.exists(img_path):
            return img_path.replace("\\", "/")
            
        try:
            from PIL import Image, ImageDraw
            img = Image.new("RGBA", (12, 12), (0, 0, 0, 0))
            draw = ImageDraw.Draw(img)
            
            hex_str = color_hex.lstrip('#')
            if len(hex_str) == 3:
                hex_str = "".join([c*2 for c in hex_str])
            r = int(hex_str[0:2], 16)
            g = int(hex_str[2:4], 16)
            b = int(hex_str[4:6], 16)
            color = (r, g, b, 255)
            
            draw.line([(2, 4), (6, 8)], fill=color, width=2)
            draw.line([(6, 8), (10, 4)], fill=color, width=2)
            
            img.save(img_path, format="PNG")
        except Exception as e:
            print(f"Error generating arrow icon: {e}")
            
        return img_path.replace("\\", "/")

    def _create_mtpe_tab(self) -> QWidget:
        from PySide6.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QSplitter, QTableWidget, QTableWidgetItem, QHeaderView, QPushButton, QGraphicsView, QGraphicsScene, QGraphicsPixmapItem, QGraphicsRectItem
        from PySide6.QtCore import Qt, QRectF
        from PySide6.QtGui import QPen, QBrush, QColor, QImage, QPixmap

        mtpe_widget = QWidget()
        layout = QVBoxLayout(mtpe_widget)
        layout.setContentsMargins(10, 10, 10, 10)
        
        splitter = QSplitter(Qt.Orientation.Horizontal)
        
        # Left side: Image and BBoxes
        self.mtpe_view = QGraphicsView()
        self.mtpe_scene = QGraphicsScene()
        self.mtpe_view.setScene(self.mtpe_scene)
        self.mtpe_view.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        
        # Right side: Text Table
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        self.mtpe_table = QTableWidget()
        self.mtpe_table.setColumnCount(2)
        self.mtpe_table.setHorizontalHeaderLabels(["Original Text", "Translated Text"])
        self.mtpe_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        
        self.mtpe_approve_btn = QPushButton("✅ Approve & Render")
        self.mtpe_approve_btn.setMinimumHeight(50)
        self.mtpe_approve_btn.setStyleSheet("""
            QPushButton {
                background-color: #10b981;
                color: white;
                font-weight: bold;
                font-size: 16px;
                border-radius: 8px;
            }
            QPushButton:hover {
                background-color: #059669;
            }
        """)
        
        right_layout.addWidget(self.mtpe_table)
        right_layout.addWidget(self.mtpe_approve_btn)
        
        self.mtpe_approve_btn.clicked.connect(self._on_mtpe_approved)
        
        splitter.addWidget(self.mtpe_view)
        splitter.addWidget(right_panel)
        splitter.setSizes([600, 400])
        
        layout.addWidget(splitter)
        
        return mtpe_widget
