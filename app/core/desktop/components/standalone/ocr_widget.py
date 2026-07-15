"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.components.standalone.ocr_widget
- RESPONSIBILITY: Standalone UI for OCR plugin.
- CALLED BY: app.core.desktop.standalone_runner
- CALLS TO: app.core.shared_registry.base
- IN = OUT: Runs OCR on image.
=============================================================================
"""
import os
import threading
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QTextEdit, 
                               QPushButton, QComboBox, QLabel, QMessageBox, QGroupBox, QFileDialog)
from PySide6.QtCore import Qt, QMetaObject, Q_ARG
from PySide6.QtGui import QPixmap
from app.core.shared_registry import DetectorFactory, RecognizerFactory
import cv2
import numpy as np

class OCRStandaloneWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.detector_instance = None
        self.recognizer_instance = None
        self.current_image_path = None
        self._setup_ui()
        self._populate_models()

    def _setup_ui(self):
        self.layout_obj = QVBoxLayout(self)
        
        # Config Area
        group_config = QGroupBox("Configuration")
        layout_config = QHBoxLayout(group_config)
        
        self.combo_detector = QComboBox()
        self.combo_recognizer = QComboBox()
        self.btn_load = QPushButton("Load Models")
        self.btn_load.clicked.connect(self._on_load_model)
        
        layout_config.addWidget(QLabel("Detector:"))
        layout_config.addWidget(self.combo_detector, stretch=1)
        layout_config.addWidget(QLabel("Recognizer:"))
        layout_config.addWidget(self.combo_recognizer, stretch=1)
        layout_config.addWidget(self.btn_load)
        
        self.layout_obj.addWidget(group_config)
        
        # Action Group
        group_action = QGroupBox("2. Process Image")
        layout_action = QVBoxLayout()
        
        self.btn_select_image = QPushButton("Select Image")
        self.btn_select_image.clicked.connect(self._on_select_image)
        layout_action.addWidget(self.btn_select_image)
        
        self.lbl_image = QLabel("No image selected")
        self.lbl_image.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.lbl_image.setMinimumSize(400, 300)
        self.lbl_image.setStyleSheet("border: 1px solid #ccc; background-color: #f0f0f0;")
        layout_action.addWidget(self.lbl_image)
        
        group_action.setLayout(layout_action)
        self.layout_obj.addWidget(group_action)
        
        # Result Group
        group_result = QGroupBox("3. Results")
        layout_result = QVBoxLayout()
        
        self.btn_run_ocr = QPushButton("Run OCR")
        self.btn_run_ocr.setEnabled(False)
        self.btn_run_ocr.clicked.connect(self._on_run_ocr)
        layout_result.addWidget(self.btn_run_ocr)
        
        self.txt_result = QTextEdit()
        self.txt_result.setReadOnly(True)
        layout_result.addWidget(self.txt_result)
        
        self.layout_obj.addWidget(group_result)

    def _populate_models(self):
        project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
        from app.core.desktop.config import ConfigLoader
        from app.core.shared_registry import DetectorFactory, RecognizerFactory
        config_loader = ConfigLoader(project_root)
        
        det_keys = DetectorFactory.get_registered_providers()
        for key in det_keys:
            label = config_loader.format_display_label(key, "offline_detector")
            state = config_loader.get_model_state(key, "offline_detector")
            if state == "NOT_SETUP":
                label += " (Not Setup)"
            elif state == "INCOMPLETE":
                label += " (Incomplete)"
            self.combo_detector.addItem(label, key)
            
        rec_keys = RecognizerFactory.get_registered_providers()
        for key in rec_keys:
            label = config_loader.format_display_label(key, "offline_ocr")
            state = config_loader.get_model_state(key, "offline_ocr")
            if state == "NOT_SETUP":
                label += " (Not Setup)"
            elif state == "INCOMPLETE":
                label += " (Incomplete)"
            self.combo_recognizer.addItem(label, key)

    def _on_load_model(self):
        det_key = self.combo_detector.currentData()
        rec_key = self.combo_recognizer.currentData()
        
        if not det_key or not rec_key:
            return
            
        self.btn_load.setEnabled(False)
        self.btn_load.setText("Loading...")
        
        def _load():
            try:
                config_dict = {"ocr": {"detector": det_key, "recognizer": rec_key}}
                
                project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))
                os.environ["PROJECT_ROOT"] = project_root
                
                from app.core.ocr.initializer import OCRInitializer
                cloud_ocr, detector, recognizer = OCRInitializer.initialize(config_dict, log_callback=None)
                
                if detector and recognizer:
                    self.detector_instance = detector
                    self.recognizer_instance = recognizer
                    QMetaObject.invokeMethod(self, "_on_load_success", Qt.ConnectionType.QueuedConnection)
                else:
                    raise Exception("Failed to load OCR models")
                    
            except Exception as e:
                QMetaObject.invokeMethod(self, "_on_load_fail", Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(e)))

        threading.Thread(target=_load, daemon=True).start()

    def _on_load_success(self):
        self.btn_load.setText("Loaded")
        if self.current_image_path:
            self.btn_run_ocr.setEnabled(True)
        QMessageBox.information(self, "Success", "Models loaded successfully!")

    def _on_load_fail(self, error_msg: str):
        self.btn_load.setEnabled(True)
        self.btn_load.setText("Load Models")
        QMessageBox.critical(self, "Error", f"Failed to load models:\n{error_msg}")

    def _on_select_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self, "Select Image", "", "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)")
        if file_path:
            self.current_image_path = file_path
            pixmap = QPixmap(file_path)
            self.lbl_image.setPixmap(pixmap.scaled(self.lbl_image.width(), self.lbl_image.height(), Qt.AspectRatioMode.KeepAspectRatio))
            if self.detector_instance and self.recognizer_instance:
                self.btn_run_ocr.setEnabled(True)

    def _on_run_ocr(self):
        if not self.detector_instance or not self.recognizer_instance or not self.current_image_path:
            return
            
        self.btn_run_ocr.setEnabled(False)
        self.btn_run_ocr.setText("Running OCR...")
        self.txt_result.clear()
        
        def _ocr():
            try:
                img = cv2.imread(self.current_image_path)
                if img is None:
                    raise Exception("Cannot read image")
                
                # Detect
                bboxes = self.detector_instance.detect(img)
                
                # Recognize
                results = []
                for box in bboxes:
                    x, y, w, h = box
                    cropped = img[y:y+h, x:x+w]
                    text = self.recognizer_instance.recognize(cropped)
                    results.append(f"Box {box}: {text}")
                    
                final_text = "\n".join(results)
                QMetaObject.invokeMethod(self, "_on_ocr_success", Qt.ConnectionType.QueuedConnection, Q_ARG(str, final_text))
            except Exception as e:
                QMetaObject.invokeMethod(self, "_on_ocr_fail", Qt.ConnectionType.QueuedConnection, Q_ARG(str, str(e)))

        threading.Thread(target=_ocr, daemon=True).start()

    def _on_ocr_success(self, text: str):
        self.txt_result.setPlainText(text)
        self.btn_run_ocr.setEnabled(True)
        self.btn_run_ocr.setText("Run OCR")

    def _on_ocr_fail(self, error_msg: str):
        self.btn_run_ocr.setEnabled(True)
        self.btn_run_ocr.setText("Run OCR")
        QMessageBox.critical(self, "Error", f"OCR failed:\n{error_msg}")
