"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.standalone.inpaint_widget
- RESPONSIBILITY: Standalone UI for Inpaint plugin.
- CALLED BY: MainWindow via direct script execution.
- CALLS TO: app.core.shared_registry (DetectorFactory, InpainterFactory)
- IN = OUT: Runs detection then inpainting on an image.
=============================================================================
"""
import os
import threading
import sys
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, 
                               QPushButton, QComboBox, QLabel, QMessageBox, QGroupBox, QFileDialog)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QPixmap, QImage
import cv2
import numpy as np

class InpaintStandaloneWidget(QWidget):
    log_signal = Signal(str, str)
    load_success_signal = Signal()
    load_fail_signal = Signal(str)
    process_success_signal = Signal(np.ndarray)
    process_fail_signal = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.detector_instance = None
        self.inpainter_instance = None
        self.current_image_path = None
        
        self.log_signal.connect(self._on_log)
        self.load_success_signal.connect(self._on_load_success)
        self.load_fail_signal.connect(self._on_load_fail)
        self.process_success_signal.connect(self._on_process_success)
        self.process_fail_signal.connect(self._on_process_fail)
        
        self._setup_ui()
        self._populate_models()

    def _setup_ui(self):
        self.layout_obj = QVBoxLayout(self)
        
        # Config Area
        group_config = QGroupBox("Configuration")
        group_config.setProperty("lang_id", "ui_configuration")
        group_config.setProperty("lang_type", "ui")
        layout_config = QHBoxLayout(group_config)
        
        self.combo_detector = QComboBox()
        self.combo_inpainter = QComboBox()
        self.btn_load = QPushButton("Load Models")
        self.btn_load.setProperty("lang_id", "ui_btn_load_models")
        self.btn_load.setProperty("lang_type", "ui")
        self.btn_load.clicked.connect(self._on_load_model)
        
        lbl_det = QLabel("Detector:")
        lbl_det.setProperty("lang_id", "ui_detector")
        lbl_det.setProperty("lang_type", "ui")
        layout_config.addWidget(lbl_det)
        layout_config.addWidget(self.combo_detector, stretch=1)
        
        lbl_inp = QLabel("Inpainter:")
        lbl_inp.setProperty("lang_id", "ui_inpainter")
        lbl_inp.setProperty("lang_type", "ui")
        layout_config.addWidget(lbl_inp)
        layout_config.addWidget(self.combo_inpainter, stretch=1)
        layout_config.addWidget(self.btn_load)
        
        self.layout_obj.addWidget(group_config)
        
        # Action Group
        group_action = QGroupBox("Select Image & Run")
        group_action.setProperty("lang_id", "ui_select_image_run")
        group_action.setProperty("lang_type", "ui")
        layout_action = QVBoxLayout()
        
        btn_layout = QHBoxLayout()
        self.btn_select_image = QPushButton("Select Image")
        self.btn_select_image.setProperty("lang_id", "ui_btn_select_image")
        self.btn_select_image.setProperty("lang_type", "ui")
        self.btn_select_image.clicked.connect(self._on_select_image)
        
        self.btn_run = QPushButton("Run Inpaint")
        self.btn_run.setProperty("lang_id", "ui_btn_run_inpaint")
        self.btn_run.setProperty("lang_type", "ui")
        self.btn_run.setEnabled(False)
        self.btn_run.clicked.connect(self._on_run)
        
        btn_layout.addWidget(self.btn_select_image)
        btn_layout.addWidget(self.btn_run)
        layout_action.addLayout(btn_layout)
        
        # Display Area
        disp_layout = QHBoxLayout()
        self.lbl_image_orig = QLabel("Original")
        self.lbl_image_orig.setProperty("lang_id", "ui_original")
        self.lbl_image_orig.setProperty("lang_type", "ui")
        self.lbl_image_orig.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image_orig.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        
        self.lbl_image_res = QLabel("Result")
        self.lbl_image_res.setProperty("lang_id", "ui_result")
        self.lbl_image_res.setProperty("lang_type", "ui")
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
            
        inp_keys = config_loader.list_field_keys("inpainter")
        for key in inp_keys:
            if key != "none":
                self.combo_inpainter.addItem(config_loader.format_display_label(key, "inpainter"), key)

    def _on_load_model(self):
        det_key = self.combo_detector.currentData()
        inp_key = self.combo_inpainter.currentData()
        
        if not det_key or not inp_key:
            return
            
        self.btn_load.setEnabled(False)
        self.btn_load.setText("Loading...")
        
        def _load():
            try:
                config_dict = {
                    "ocr": {"detector": det_key},
                    "inpainter": {"inpainter": inp_key, "enable_advanced_diffusion": False},
                    "pipeline": {"enable_inpainter": True}
                }
                project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../../../"))
                os.environ["PROJECT_ROOT"] = project_root
                
                from app.core.ocr.initializer import OCRInitializer
                from app.core.inpainter.initializer import InpainterInitializer
                
                _, det, _ = OCRInitializer.initialize(config_dict, log_callback=self._log)
                inp, _, _, _ = InpainterInitializer.initialize(config_dict, log_callback=self._log)
                
                if det and inp:
                    self.detector_instance = det
                    self.inpainter_instance = inp
                    self.load_success_signal.emit()
                else:
                    raise Exception("Failed to initialize models.")
            except Exception as e:
                self.load_fail_signal.emit(str(e))

        threading.Thread(target=_load, daemon=True).start()

    def _on_load_success(self):
        self.btn_load.setText("Loaded")
        if self.current_image_path:
            self.btn_run.setEnabled(True)
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
            
            if self.detector_instance and self.inpainter_instance:
                self.btn_run.setEnabled(True)

    def _on_run(self):
        if not self.current_image_path or not self.detector_instance or not self.inpainter_instance:
            return
            
        self.btn_run.setEnabled(False)
        self.btn_run.setText("Processing...")
        
        def _process():
            try:
                img = cv2.imread(self.current_image_path)
                if img is None:
                    raise Exception("Could not read image file.")
                    
                bboxes, _, _, _ = self.detector_instance.detect(img)
                if not bboxes:
                    # No boxes, just return the original image
                    self.process_success_signal.emit(img)
                    return
                    
                res_img = self.inpainter_instance.inpaint(img, bboxes)
                self.process_success_signal.emit(res_img)
            except Exception as e:
                self.process_fail_signal.emit(str(e))

        threading.Thread(target=_process, daemon=True).start()

    def _on_process_success(self, res_img: np.ndarray):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("Run Inpaint")
        
        # Convert cv2 image to QPixmap
        res_rgb = cv2.cvtColor(res_img, cv2.COLOR_BGR2RGB)
        h, w, ch = res_rgb.shape
        bytes_per_line = ch * w
        qimg = QImage(res_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(qimg)
        scaled = pixmap.scaled(self.lbl_image_res.size(), Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        self.lbl_image_res.setPixmap(scaled)

    def _on_process_fail(self, error_msg: str):
        self.btn_run.setEnabled(True)
        self.btn_run.setText("Run Inpaint")
        QMessageBox.critical(self, "Error", f"Processing failed:\n{error_msg}")


if __name__ == "__main__":
    workspace_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))))
    if workspace_root not in sys.path:
        sys.path.insert(0, workspace_root)
        
    os.environ["TARGET_PLUGIN_DIRS"] = "detector,inpainter"
    
    from PySide6.QtWidgets import QApplication
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = InpaintStandaloneWidget()
    window.resize(1000, 600)
    window.setWindowTitle("Standalone Inpaint")
    window.show()
    print("STANDALONE_READY", flush=True)
    sys.exit(app.exec())
