"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.widget_factory.layout_builder.preview_tester
- RESPONSIBILITY: Build the "Preview Tester" tab and its sub-tabs.
- CALLED BY: app.core.desktop.components.widget_factory.layout_builder.__init__ (as Mixin)
- CALLS TO: PySide6.QtWidgets, QGraphicsView, QTableWidget
- IN = OUT: Returns QWidget containing the preview tester layout and stores refs in self.mw.
=============================================================================
"""
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QPushButton, QCheckBox, QLabel,
    QSplitter
)
from app.core.desktop.components.preview_widgets.interactive_canvas import InteractivePreviewCanvas
from app.core.desktop.components.preview_widgets.inspector_panel import InspectorPanel
from PySide6.QtCore import Qt

class PreviewTesterBuilderMixin:
    def create_preview_tester_tab(self) -> QWidget:
        container = QWidget()
        layout = QVBoxLayout(container)

        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        load_button = QPushButton("Load Test Image...")
        load_button.setProperty("lang_id", "ui_load_test_image")
        load_button.setProperty("lang_type", "ui")
        load_button.clicked.connect(self.mw._load_test_image)

        self.mw.fast_preview_check = QCheckBox("Fast Preview")
        self.mw.fast_preview_check.setProperty("lang_id", "ui_fast_preview")
        self.mw.fast_preview_check.setProperty("lang_type", "ui")
        self.mw.fast_preview_check.setChecked(True)

        run_test_text = self.mw.get_string("ui_run_test") if self.mw.get_string("ui_run_test") != "ui_run_test" else "Run Test"
        self.mw.run_test_button = QPushButton(run_test_text)
        self.mw.run_test_button.setProperty("lang_id", "ui_run_test")
        self.mw.run_test_button.setProperty("lang_type", "ui")
        self.mw.run_test_button.setEnabled(False)
        self.mw.run_test_button.clicked.connect(self.mw.preview_tester.run_visual_test_thread)

        reset_button = QPushButton("Reset View")
        reset_button.setProperty("lang_id", "ui_reset_view")
        reset_button.setProperty("lang_type", "ui")
        reset_button.clicked.connect(self.mw._fit_image_to_view)

        self.mw.zoom_label = QLabel("Zoom: 100%")

        self.mw.limit_zoom_check = QCheckBox("Limit Zoom")
        self.mw.limit_zoom_check.setChecked(True)
        self.mw.limit_zoom_check.setToolTip("When checked, zoom is limited between 5% and 800%.")

        from PySide6.QtWidgets import QButtonGroup, QRadioButton
        self.mw.mode_group = QButtonGroup(self.mw)
        self.mw.btn_mode_select = QRadioButton("Select")
        self.mw.btn_mode_select.setChecked(True)
        self.mw.btn_mode_draw = QRadioButton("Draw Box")
        self.mw.mode_group.addButton(self.mw.btn_mode_select, 0)
        self.mw.mode_group.addButton(self.mw.btn_mode_draw, 1)
        
        def _on_mode_changed(idx):
            mode = "select" if idx == 0 else "draw"
            self.mw.preview_canvas.set_mode(mode)
            
        self.mw.mode_group.idClicked.connect(_on_mode_changed)

        controls_layout.addWidget(load_button)
        controls_layout.addWidget(self.mw.fast_preview_check)
        controls_layout.addWidget(self.mw.btn_mode_select)
        controls_layout.addWidget(self.mw.btn_mode_draw)
        controls_layout.addStretch()
        controls_layout.addWidget(self.mw.zoom_label)
        controls_layout.addWidget(reset_button)
        controls_layout.addWidget(self.mw.run_test_button)

        layout.addWidget(controls_frame)

        self.mw.preview_splitter = QSplitter(Qt.Orientation.Horizontal)
        
        from app.core.desktop.components.preview_widgets.file_explorer_panel import FileExplorerPanel
        self.mw.file_explorer = FileExplorerPanel()
        
        self.mw.preview_canvas = InteractivePreviewCanvas()
        self.mw.preview_inspector = InspectorPanel()
        
        self.mw.preview_splitter.addWidget(self.mw.file_explorer)
        self.mw.preview_splitter.addWidget(self.mw.preview_canvas)
        self.mw.preview_splitter.addWidget(self.mw.preview_inspector)
        
        self.mw.preview_splitter.setStretchFactor(0, 1)
        self.mw.preview_splitter.setStretchFactor(1, 4)
        self.mw.preview_splitter.setStretchFactor(2, 1)
        
        layout.addWidget(self.mw.preview_splitter, stretch=1)
        
        # Override wheel event for zooming
        self.mw.preview_canvas.wheelEvent = self.mw._wheel_event_zoom

        self.mw.preview_canvas.box_selected.connect(self.mw.preview_tester.on_box_selected)
        self.mw.file_explorer.file_selected.connect(self.mw.preview_tester.load_test_image_from_path)
        self.mw.preview_canvas.box_created.connect(self.mw.preview_tester.on_box_created)
        
        self.mw.preview_inspector.btn_rerun_ocr.clicked.connect(self.mw.preview_tester.run_single_box_ocr)
        self.mw.preview_inspector.btn_rerun_trans.clicked.connect(self.mw.preview_tester.run_single_box_translation)
        self.mw.preview_inspector.btn_render_box.clicked.connect(self.mw.preview_tester.run_single_box_render)

        return container
