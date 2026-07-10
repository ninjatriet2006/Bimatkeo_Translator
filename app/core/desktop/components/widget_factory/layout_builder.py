from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QPushButton, QScrollArea, QColorDialog,
    QTabWidget, QGraphicsView, QGraphicsScene, QTableWidget, QHeaderView, QCheckBox, QProgressBar
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QColor

from app.core.desktop.components.widgets_helper import SearchableComboBox
from app.core.desktop.components.ui_utils import build_grouped_settings_tabs

class LayoutBuilderFactory:
    def __init__(self, main_window):
        self.mw = main_window

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

    def create_setting_row(self, info: dict, context_key: str = None) -> QWidget:
        row_widget = QWidget()
        row_layout = QHBoxLayout(row_widget)
        row_layout.setContentsMargins(0, 0, 0, 0)
        row_layout.setSpacing(5)

        widget_type = info.get("widget")

        if widget_type == "label":
            widget = QLabel(info.get("label", ""))
            if "style" in info:
                widget.setStyleSheet(info["style"])
            row_layout.addWidget(widget)
            if not context_key:
                self.mw.setting_widgets[info['key']] = widget
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

            label_text = info.get("label", info.get("key", "N/A"))
            main_label = QLabel(label_text)
            label_layout.addWidget(main_label)

            tooltip_text = info.get("tooltip")
            if tooltip_text:
                tooltip_icon = QLabel("(?)")
                tooltip_icon.setStyleSheet("color: #40E0D0;")
                tooltip_icon.setCursor(Qt.CursorShape.PointingHandCursor)
                default_val = info.get('default', 'N/A')
                full_tooltip = f"<b>{label_text}</b><hr>{tooltip_text}<br><i>(Default: {default_val})</i>"
                tooltip_icon.setToolTip(full_tooltip)
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
                        from app.core.desktop.recommend import get_recommended_size
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

    def update_translator_tooltip(self, translator_name: str):
        import app.core.main_window as mw_module
        category = self.mw._get_active_translator_category()
        key = 'offline_translator' if category == 'offline' else 'ai_translator'
        translator_combo = self.mw.setting_widgets.get(key)
        if not translator_combo:
            return

        from app.core.shared_registry import TranslatorFactory
        capabilities = TranslatorFactory.get_capabilities(translator_name)
        code_to_name = {v: k for k, v in mw_module.LANGUAGES.items()}

        label = self.mw.config_loader.format_display_label(translator_name, key)
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

    def handle_widget_button_click(self, key: str, associated_widget: QWidget):
        if key in ["font_color", "outline_color"]:
            current_color = associated_widget.text()
            if not current_color: current_color = "000000" if key == "font_color" else "FFFFFF"
            title = "Choose Font Color" if key == "font_color" else "Choose Outline Color"
            color = QColorDialog.getColor(initial=f"#{current_color}", title=title)
            if color.isValid():
                new_color_hex = color.name()[1:]
                associated_widget.setText(new_color_hex)
                self.mw._on_setting_changed(key)
        
        elif key == "ai_model":
            button = associated_widget.parent().findChild(QPushButton)
            if button:
                self.mw._fetch_ai_models(button)

    def create_bottom_panel(self) -> QWidget:
        bottom_frame = QFrame()
        bottom_frame.setFrameShape(QFrame.Shape.NoFrame)
        layout = QHBoxLayout(bottom_frame)
        layout.setContentsMargins(0, 0, 0, 0)

        progress_widget = QWidget()
        progress_layout = QHBoxLayout(progress_widget)
        progress_layout.setSpacing(10)
        progress_layout.setContentsMargins(5, 5, 5, 5)

        self.mw.progress_label = QLabel("Ready")
        self.mw.progress_label.setMinimumWidth(200)

        self.mw.progress_bar = QProgressBar()
        self.mw.progress_bar.setValue(0)
        self.mw.progress_bar.setTextVisible(False)
        self.mw.progress_bar.setFormat("%p% - %v/%m pages")

        progress_layout.addWidget(self.mw.progress_label)
        progress_layout.addWidget(self.mw.progress_bar, stretch=1)

        self.mw.start_button = QPushButton("▶️ START")
        self.mw.start_button.clicked.connect(self.mw._start_pipeline_thread)
        self.mw.start_button.setFixedHeight(40)
        font = self.mw.start_button.font()
        font.setBold(True)
        self.mw.start_button.setFont(font)

        self.mw.stop_button = QPushButton("⏹️ STOP")
        self.mw.stop_button.clicked.connect(self.mw._stop_pipeline)
        self.mw.stop_button.setEnabled(False)
        self.mw.stop_button.setFixedHeight(40)
        stop_font = self.mw.stop_button.font()
        stop_font.setBold(True)
        self.mw.stop_button.setFont(stop_font)

        layout.addWidget(progress_widget, stretch=1)
        layout.addWidget(self.mw.start_button)
        layout.addWidget(self.mw.stop_button)

        return bottom_frame

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

    def create_preview_tester_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        load_button = QPushButton("Load Test Image...")
        load_button.clicked.connect(self.mw._load_test_image)

        self.mw.fast_preview_check = QCheckBox("Fast Preview")
        self.mw.fast_preview_check.setChecked(True)

        self.mw.run_test_button = QPushButton("Run Test")
        self.mw.run_test_button.setEnabled(False)
        self.mw.run_test_button.clicked.connect(self.mw._run_visual_test_thread)

        reset_button = QPushButton("Reset View")
        reset_button.clicked.connect(self.mw._fit_image_to_view)

        self.mw.zoom_label = QLabel("Zoom: 100%")

        self.mw.limit_zoom_check = QCheckBox("Limit Zoom")
        self.mw.limit_zoom_check.setChecked(True)
        self.mw.limit_zoom_check.setToolTip("When checked, zoom is limited between 5% and 800%.")

        controls_layout.addWidget(load_button)
        controls_layout.addWidget(self.mw.fast_preview_check)
        controls_layout.addStretch()
        controls_layout.addWidget(self.mw.zoom_label)
        controls_layout.addWidget(reset_button)
        controls_layout.addWidget(self.mw.run_test_button)

        layout.addWidget(controls_frame)

        self.mw.preview_tabs = QTabWidget()
        
        self.mw.tab_detector = QWidget()
        det_layout = QVBoxLayout(self.mw.tab_detector)
        self.mw.btn_export_detector = QPushButton("💾 Export Image with BBox")
        self.mw.btn_export_detector.clicked.connect(self.mw._export_detector_image)
        det_layout.addWidget(self.mw.btn_export_detector, alignment=Qt.AlignmentFlag.AlignRight)
        self.mw.view_detector = QGraphicsView()
        self.mw.scene_detector = QGraphicsScene()
        self.mw.view_detector.setScene(self.mw.scene_detector)
        self.mw.view_detector.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        det_layout.addWidget(self.mw.view_detector)
        self.mw.preview_tabs.addTab(self.mw.tab_detector, "Detector")

        self.mw.tab_ocr = QWidget()
        ocr_layout = QVBoxLayout(self.mw.tab_ocr)
        self.mw.btn_export_ocr = QPushButton("💾 Export OCR Data (CSV)")
        self.mw.btn_export_ocr.clicked.connect(self.mw._export_ocr_data)
        ocr_layout.addWidget(self.mw.btn_export_ocr, alignment=Qt.AlignmentFlag.AlignRight)
        self.mw.table_ocr = QTableWidget()
        self.mw.table_ocr.setColumnCount(2)
        self.mw.table_ocr.setHorizontalHeaderLabels(["BBox", "Original Text"])
        self.mw.table_ocr.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ocr_layout.addWidget(self.mw.table_ocr)
        self.mw.preview_tabs.addTab(self.mw.tab_ocr, "OCR")

        self.mw.tab_translator = QWidget()
        trans_layout = QVBoxLayout(self.mw.tab_translator)
        self.mw.btn_export_translator = QPushButton("💾 Export Translated Text (CSV)")
        self.mw.btn_export_translator.clicked.connect(self.mw._export_translator_data)
        trans_layout.addWidget(self.mw.btn_export_translator, alignment=Qt.AlignmentFlag.AlignRight)
        self.mw.table_translator = QTableWidget()
        self.mw.table_translator.setColumnCount(2)
        self.mw.table_translator.setHorizontalHeaderLabels(["Original Text", "Translated Text"])
        self.mw.table_translator.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        trans_layout.addWidget(self.mw.table_translator)
        self.mw.preview_tabs.addTab(self.mw.tab_translator, "Translator")

        self.mw.tab_inpainter = QWidget()
        inp_layout = QVBoxLayout(self.mw.tab_inpainter)
        self.mw.btn_export_inpainter = QPushButton("💾 Export Inpainted Image")
        self.mw.btn_export_inpainter.clicked.connect(self.mw._export_inpainter_image)
        inp_layout.addWidget(self.mw.btn_export_inpainter, alignment=Qt.AlignmentFlag.AlignRight)
        self.mw.view_inpainter = QGraphicsView()
        self.mw.scene_inpainter = QGraphicsScene()
        self.mw.view_inpainter.setScene(self.mw.scene_inpainter)
        self.mw.view_inpainter.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        inp_layout.addWidget(self.mw.view_inpainter)
        self.mw.preview_tabs.addTab(self.mw.tab_inpainter, "Image Inpainter")

        self.mw.tab_render = QWidget()
        ren_layout = QVBoxLayout(self.mw.tab_render)
        self.mw.btn_export_render = QPushButton("💾 Export Rendered Image")
        self.mw.btn_export_render.clicked.connect(self.mw._export_render_image)
        ren_layout.addWidget(self.mw.btn_export_render, alignment=Qt.AlignmentFlag.AlignRight)
        self.mw.view_render = QGraphicsView()
        self.mw.scene_render = QGraphicsScene()
        self.mw.view_render.setScene(self.mw.scene_render)
        self.mw.view_render.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        ren_layout.addWidget(self.mw.view_render)
        self.mw.preview_tabs.addTab(self.mw.tab_render, "Render Output")

        self.mw.view_detector.wheelEvent = self.mw._wheel_event_zoom
        self.mw.view_inpainter.wheelEvent = self.mw._wheel_event_zoom
        self.mw.view_render.wheelEvent = self.mw._wheel_event_zoom
        
        views = [self.mw.view_detector, self.mw.view_inpainter, self.mw.view_render]
        for i in range(len(views)):
            for j in range(len(views)):
                if i != j:
                    views[i].horizontalScrollBar().valueChanged.connect(views[j].horizontalScrollBar().setValue)
                    views[i].verticalScrollBar().valueChanged.connect(views[j].verticalScrollBar().setValue)

        layout.addWidget(self.mw.preview_tabs, stretch=1)

        self.mw.original_view = self.mw.view_detector
        self.mw.original_scene = self.mw.scene_detector
        self.mw.translated_view = self.mw.view_render
        self.mw.translated_scene = self.mw.scene_render

        return container
