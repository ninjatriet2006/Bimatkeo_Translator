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
    QTabWidget, QGraphicsView, QGraphicsScene, QTableWidget, QHeaderView
)
from PySide6.QtCore import Qt

class PreviewTesterBuilderMixin:
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
