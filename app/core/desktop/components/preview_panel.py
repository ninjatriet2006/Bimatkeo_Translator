from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QFrame, 
                               QPushButton, QCheckBox, QLabel, QTabWidget, 
                               QGraphicsView, QGraphicsScene, QTableWidget, QHeaderView)
from PySide6.QtCore import Qt

class PreviewPanel(QWidget):
    """UI Component for the Preview Tester tab."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # 1. Top Controls Panel
        controls_frame = QFrame()
        controls_layout = QHBoxLayout(controls_frame)

        self.load_button = QPushButton("Load Test Image...")
        
        self.fast_preview_check = QCheckBox("Fast Preview")
        self.fast_preview_check.setChecked(True)

        self.run_test_button = QPushButton("Run Test")
        self.run_test_button.setEnabled(False)

        self.reset_button = QPushButton("Reset View")
        
        self.zoom_label = QLabel("Zoom: 100%")

        self.limit_zoom_check = QCheckBox("Limit Zoom")
        self.limit_zoom_check.setChecked(True)
        self.limit_zoom_check.setToolTip("When checked, zoom is limited between 5% and 800%.")

        controls_layout.addWidget(self.load_button)
        controls_layout.addWidget(self.fast_preview_check)
        controls_layout.addStretch()
        controls_layout.addWidget(self.zoom_label)
        controls_layout.addWidget(self.reset_button)
        controls_layout.addWidget(self.run_test_button)

        layout.addWidget(controls_frame)

        # 2. Sub-tabs for Preview Tester
        self.preview_tabs = QTabWidget()
        
        # Detector Tab
        self.tab_detector = QWidget()
        det_layout = QVBoxLayout(self.tab_detector)
        self.btn_export_detector = QPushButton("💾 Export Image with BBox")
        det_layout.addWidget(self.btn_export_detector, alignment=Qt.AlignmentFlag.AlignRight)
        self.view_detector = QGraphicsView()
        self.scene_detector = QGraphicsScene()
        self.view_detector.setScene(self.scene_detector)
        self.view_detector.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        det_layout.addWidget(self.view_detector)
        self.preview_tabs.addTab(self.tab_detector, "Detector")

        # OCR Tab
        self.tab_ocr = QWidget()
        ocr_layout = QVBoxLayout(self.tab_ocr)
        self.btn_export_ocr = QPushButton("💾 Export OCR Data (CSV)")
        ocr_layout.addWidget(self.btn_export_ocr, alignment=Qt.AlignmentFlag.AlignRight)
        self.table_ocr = QTableWidget()
        self.table_ocr.setColumnCount(2)
        self.table_ocr.setHorizontalHeaderLabels(["BBox", "Original Text"])
        self.table_ocr.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        ocr_layout.addWidget(self.table_ocr)
        self.preview_tabs.addTab(self.tab_ocr, "OCR")

        # Translator Tab
        self.tab_translator = QWidget()
        trans_layout = QVBoxLayout(self.tab_translator)
        self.btn_export_translator = QPushButton("💾 Export Translated Text (CSV)")
        trans_layout.addWidget(self.btn_export_translator, alignment=Qt.AlignmentFlag.AlignRight)
        self.table_translator = QTableWidget()
        self.table_translator.setColumnCount(2)
        self.table_translator.setHorizontalHeaderLabels(["Original Text", "Translated Text"])
        self.table_translator.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        trans_layout.addWidget(self.table_translator)
        self.preview_tabs.addTab(self.tab_translator, "Translator")

        # Inpainter Tab
        self.tab_inpainter = QWidget()
        inp_layout = QVBoxLayout(self.tab_inpainter)
        self.btn_export_inpainter = QPushButton("💾 Export Inpainted Image")
        inp_layout.addWidget(self.btn_export_inpainter, alignment=Qt.AlignmentFlag.AlignRight)
        self.view_inpainter = QGraphicsView()
        self.scene_inpainter = QGraphicsScene()
        self.view_inpainter.setScene(self.scene_inpainter)
        self.view_inpainter.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        inp_layout.addWidget(self.view_inpainter)
        self.preview_tabs.addTab(self.tab_inpainter, "Image Inpainter")

        # Render Output Tab
        self.tab_render = QWidget()
        ren_layout = QVBoxLayout(self.tab_render)
        self.btn_export_render = QPushButton("💾 Export Rendered Image")
        ren_layout.addWidget(self.btn_export_render, alignment=Qt.AlignmentFlag.AlignRight)
        self.view_render = QGraphicsView()
        self.scene_render = QGraphicsScene()
        self.view_render.setScene(self.scene_render)
        self.view_render.setDragMode(QGraphicsView.DragMode.ScrollHandDrag)
        ren_layout.addWidget(self.view_render)
        self.preview_tabs.addTab(self.tab_render, "Render Output")

        layout.addWidget(self.preview_tabs)

    def link_scrollbars(self):
        """Synchronize panning across image views."""
        for sb_name in ['horizontalScrollBar', 'verticalScrollBar']:
            det_sb = getattr(self.view_detector, sb_name)()
            inp_sb = getattr(self.view_inpainter, sb_name)()
            ren_sb = getattr(self.view_render, sb_name)()
            det_sb.valueChanged.connect(inp_sb.setValue)
            det_sb.valueChanged.connect(ren_sb.setValue)
            inp_sb.valueChanged.connect(det_sb.setValue)
            inp_sb.valueChanged.connect(ren_sb.setValue)
            ren_sb.valueChanged.connect(det_sb.setValue)
            ren_sb.valueChanged.connect(inp_sb.setValue)
