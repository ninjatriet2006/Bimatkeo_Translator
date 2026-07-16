"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.standalone.render_widget
- RESPONSIBILITY: Standalone UI for Renderer plugin.
- CALLED BY: MainWindow via direct script execution.
- CALLS TO: app.core.shared_registry (DetectorFactory, RecognizerFactory, RendererFactory)
- IN = OUT: Detects, recognizes, and renders text over an image.
=============================================================================
"""
import os
import threading
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit,
                               QPushButton, QComboBox, QLabel, QMessageBox, QGroupBox, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
import cv2
import numpy as np

class RenderStandaloneWidget(QWidget):
    log_signal = Signal(str, str)
    load_success_signal = Signal()
    load_fail_signal = Signal(str)
    pre_process_success_signal = Signal(list, list)
    process_success_signal = Signal(np.ndarray)
    process_fail_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.detector_instance = None
        self.recognizer_instance = None
        self.renderer_instance = None
        self.current_image_path = None
        self.last_bboxes = []
        
        self.log_signal.connect(self._on_log)
        self.load_success_signal.connect(self._on_load_success)
        self.load_fail_signal.connect(self._on_load_fail)
        self.pre_process_success_signal.connect(self._on_pre_process_success)
        self.process_success_signal.connect(self._on_process_success)
        self.process_fail_signal.connect(self._on_process_fail)
        
        self._setup_ui()
        self._populate_models()

    def _setup_ui(self):
        self.layout_obj = QVBoxLayout(self)
        
        # Config Area
        group_config = QGroupBox("Configuration")
        layout_config = QHBoxLayout(group_config)
        
        self.combo_detector = QComboBox()
        self.combo_recognizer = QComboBox()
        self.combo_renderer = QComboBox()
        self.btn_load = QPushButton("Load Models")
        self.btn_load.clicked.connect(self._on_load_model)
        
        layout_config.addWidget(QLabel("Det:"))
        layout_config.addWidget(self.combo_detector)
        layout_config.addWidget(QLabel("Rec:"))
        layout_config.addWidget(self.combo_recognizer)
        layout_config.addWidget(QLabel("Render:"))
        layout_config.addWidget(self.combo_renderer)
        layout_config.addWidget(self.btn_load)
        
        self.layout_obj.addWidget(group_config)
        
        # Action Group
        group_action = QGroupBox("Select Image & Texts")
        layout_action = QVBoxLayout()
        
        self.btn_select_image = QPushButton("1. Select Image (Auto-Detect Text)")
        self.btn_select_image.clicked.connect(self._on_select_image)
        layout_action.addWidget(self.btn_select_image)
        
        self.txt_lines = QTextEdit()
        self.txt_lines.setPlaceholderText("Detected text will appear here. Edit as needed, one line per bounding box.")
        layout_action.addWidget(self.txt_lines)
        
        self.btn_run = QPushButton("2. Run Render")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self._on_run)
        layout_action.addWidget(self.btn_run)
        
        # Display Area
        disp_layout = QHBoxLayout()
        self.lbl_image_orig = QLabel("Original")
        self.lbl_image_orig.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image_orig.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        self.lbl_image_res = QLabel("Result")
        self.lbl_image_res.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image_res.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        disp_layout.addWidget(self.lbl_image_orig)
        disp_layout.addWidget(self.lbl_image_res)
        
        layout_action.addLayout(disp_layout)
        group_action.setLayout(layout_action)
        self.layout_obj.addWidget(group_action, stretch=1)

    def _log(self, level: str, msg: str):
        self.log_signal.emit(level, msg)

    def _on_log(self, level: str, msg: str):
        print(f"[{level}] {msg}")

    def _populate_models(self):
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
        from app.core.desktop.config import ConfigLoader
        config_loader = ConfigLoader(project_root)
        
        det_keys = config_loader.list_field_keys("offline_detector")
        for key in det_keys:
            self.combo_detector.addItem(config_loader.format_display_label(key, "offline_detector"), key)
            
        rec_keys = config_loader.list_field_keys("offline_ocr")
        for key in rec_keys:
            self.combo_recognizer.addItem(config_loader.format_display_label(key, "offline_ocr"), key)
            
        ren_keys = config_loader.list_field_keys("render")
        for key in ren_keys:
            if key != "none":
                self.combo_renderer.addItem(config_loader.format_display_label(key, "render"), key)

    def _on_load_model(self):
        det_key = self.combo_detector.currentData()
        rec_key = self.combo_recognizer.currentData()
        ren_key = self.combo_renderer.currentData()
        
        if not det_key or not rec_key or not ren_key:
            return
            
        self.btn_load.setEnabled(False)
        self.btn_load.setText("Loading...")
        
        def _load():
            try:
                config_dict = {
                    "ocr": {"detector": det_key, "recognizer": rec_key},
                    "render": {"renderer": ren_key},
                    "pipeline": {"enable_renderer": True}
                }
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
                os.environ["PROJECT_ROOT"] = project_root
                
                from app.core.ocr.initializer import OCRInitializer
                from app.core.renderer.initializer import RendererInitializer
                
                _, det, rec = OCRInitializer.initialize(config_dict, log_callback=self._log)
                ren = RendererInitializer.initialize(config_dict, log_callback=self._log)
                
                if det and rec and ren:
                    self.detector_instance = det
                    self.recognizer_instance = rec
                    self.renderer_instance = ren
                    self.load_success_signal.emit()
                else:
                    raise Exception("Failed to initialize models.")
            except Exception as e:
                self.load_fail_signal.emit(str(e))

        threading.Thread(target=_load, daemon=True).start()

    def _on_load_success(self):
        self.btn_load.setText("Loaded")
        QMessageBox.information(self, "Success", "Models loaded successfully!")

    def _on_load_fail(self, error_msg: str):
        self.btn_load.setEnabled(True)
        self.btn_load.setText("Load Models")
        QMessageBox.critical(self, "Error", f"Failed to load models:\n{error_msg}")

    def _on_select_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Images (*.png *.jpg *.jpeg *.bmp)")
        if path:
            self.current_image_path = path
            pixmap = QPixmap(path)
            scaled = pixmap.scaled(self.lbl_image_orig.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
            self.lbl_image_orig.setPixmap(scaled)
            self.lbl_image_res.clear()
            self.txt_lines.clear()
            
            if self.detector_instance and self.recognizer_instance:
                self.btn_run.setEnabled(False)
                self.btn_select_image.setText("Extracting text...")
                
                def _extract():
                    try:
                        img = cv2.imread(self.current_image_path)
                        bboxes, _, _, _ = self.detector_instance.detect(img)
                        if not bboxes:
                            self.pre_process_success_signal.emit([], [])
                            return
                        texts, _, _ = self.recognizer_instance.recognize(img, bboxes)
                        self.pre_process_success_signal.emit(bboxes, texts)
                    except Exception as e:
                        self.process_fail_signal.emit(str(e))
                        
                threading.Thread(target=_extract, daemon=True).start()

    def _on_pre_process_success(self, bboxes: list, texts: list):
        self.btn_select_image.setText("1. Select Image (Auto-Detect Text)")
        self.last_bboxes = bboxes
        self.txt_lines.setPlainText("\\n".join(texts))
        if self.renderer_instance:
            self.btn_run.setEnabled(True)

    def _on_run(self):
        if not self.current_image_path or not self.renderer_instance or not self.last_bboxes:
            return
            
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Rendering...")
        
        texts_input = self.txt_lines.toPlainText().split("\\n")
        # pad if user deleted some lines
        while len(texts_input) < len(self.last_bboxes):
            texts_input.append("")
        texts_input = texts_input[:len(self.last_bboxes)]
        
        def _process():
            try:
                img = cv2.imread(self.current_image_path)
                if img is None:
                    raise Exception("Could not read image file.")
                    
                res_img = self.renderer_instance.render(img, self.last_bboxes, texts_input)
                self.process_success_signal.emit(res_img)
            except Exception as e:
                self.process_fail_signal.emit(str(e))

        threading.Thread(target=_process, daemon=True).start()

    def _on_process_success(self, res_img: np.ndarray):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("2. Run Render")
        
        res_rgb = cv2.cvtColor(res_img, cv2.COLOR_BGR2RGB)
        h, w, ch = res_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(res_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(self.lbl_image_res.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.lbl_image_res.setPixmap(scaled)

    def _on_process_fail(self, error_msg: str):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("2. Run Render")
        QMessageBox.critical(self, "Error", f"Processing failed:\n{error_msg}")


if __name__ == "__main__":
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)
        
    os.environ["TARGET_PLUGIN_DIRS"] = "detector,recognizer,renderer"
    
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = RenderStandaloneWidget()
    window.resize(1000, 700)
    window.setWindowTitle("Standalone Render")
    window.show()
    sys.exit(app.exec())
