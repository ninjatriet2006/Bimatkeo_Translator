"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.export_manager
- RESPONSIBILITY: Handle exporting various test results (detector, inpainter, render, etc.)
- CALLED BY: app.core.desktop.logic.core_handlers.export
- CALLS TO: PySide6.QtWidgets, os, shutil, json, csv
- IN = OUT: Reads test output states and copies them to user-selected paths.
=============================================================================
"""
import os
import shutil
import json
import csv
from PySide6.QtWidgets import QMessageBox, QFileDialog

class ExportManager:
    def __init__(self, main_window):
        self.mw = main_window

    def export_detector_image(self):
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            QMessageBox.warning(self.mw, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        source_file = os.path.join(self.mw.current_test_output_dir, "test_detector.png")
        if not os.path.exists(source_file):
            QMessageBox.warning(self.mw, "Export Error", "Detector result image not found.")
            return
            
        save_path, _ = QFileDialog.getSaveFileName(self.mw, "Export Detector Image", "detector_result.png", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                QMessageBox.information(self.mw, "Success", "Detector image exported successfully.")
            except Exception as e:
                QMessageBox.critical(self.mw, "Error", f"Failed to export image: {str(e)}")

    def export_ocr_data(self):
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            QMessageBox.warning(self.mw, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        source_file = os.path.join(self.mw.current_test_output_dir, "test_data.json")
        if not os.path.exists(source_file):
            QMessageBox.warning(self.mw, "Export Error", "OCR data not found.")
            return
            
        save_path, _ = QFileDialog.getSaveFileName(self.mw, "Export OCR Data", "ocr_data.csv", "CSV Files (*.csv)")
        if save_path:
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                bboxes = data.get("bboxes", [])
                original_texts = data.get("original_texts", [])
                
                with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["BBox", "Original Text"])
                    for i in range(max(len(bboxes), len(original_texts))):
                        box = str(bboxes[i]) if i < len(bboxes) else ""
                        text = original_texts[i] if i < len(original_texts) else ""
                        writer.writerow([box, text])
                QMessageBox.information(self.mw, "Success", "OCR data exported successfully.")
            except Exception as e:
                QMessageBox.critical(self.mw, "Error", f"Failed to export OCR data: {str(e)}")

    def export_translator_data(self):
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            QMessageBox.warning(self.mw, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        source_file = os.path.join(self.mw.current_test_output_dir, "test_data.json")
        if not os.path.exists(source_file):
            QMessageBox.warning(self.mw, "Export Error", "Translation data not found.")
            return
            
        save_path, _ = QFileDialog.getSaveFileName(self.mw, "Export Translated Text", "translated_text.csv", "CSV Files (*.csv)")
        if save_path:
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                original_texts = data.get("original_texts", [])
                translated_texts = data.get("translated_texts", [])
                
                with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    writer.writerow(["Original Text", "Translated Text"])
                    for i in range(max(len(original_texts), len(translated_texts))):
                        orig = original_texts[i] if i < len(original_texts) else ""
                        trans = translated_texts[i] if i < len(translated_texts) else ""
                        writer.writerow([orig, trans])
                QMessageBox.information(self.mw, "Success", "Translated text exported successfully.")
            except Exception as e:
                QMessageBox.critical(self.mw, "Error", f"Failed to export translated text: {str(e)}")

    def export_inpainter_image(self):
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            QMessageBox.warning(self.mw, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        source_file = os.path.join(self.mw.current_test_output_dir, "test_inpainter.png")
        if not os.path.exists(source_file):
            QMessageBox.warning(self.mw, "Export Error", "Inpainter result image not found.")
            return
            
        save_path, _ = QFileDialog.getSaveFileName(self.mw, "Export Inpainted Image", "inpainter_result.png", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                QMessageBox.information(self.mw, "Success", "Inpainted image exported successfully.")
            except Exception as e:
                QMessageBox.critical(self.mw, "Error", f"Failed to export image: {str(e)}")

    def export_render_image(self):
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            QMessageBox.warning(self.mw, "Export Error", "No test results available to export. Please run a test first.")
            return
            
        if not hasattr(self.mw, 'test_image_path') or not self.mw.test_image_path:
            QMessageBox.warning(self.mw, "Export Error", "No test image path found.")
            return
            
        original_filename = os.path.basename(self.mw.test_image_path)
        output_filename = os.path.splitext(original_filename)[0] + ".png"
        source_file = os.path.join(self.mw.current_test_output_dir, output_filename)
        
        if not os.path.exists(source_file):
            QMessageBox.warning(self.mw, "Export Error", "Render result image not found.")
            return
            
        save_path, _ = QFileDialog.getSaveFileName(self.mw, "Export Rendered Image", f"{output_filename}", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                QMessageBox.information(self.mw, "Success", "Rendered image exported successfully.")
            except Exception as e:
                QMessageBox.critical(self.mw, "Error", f"Failed to export image: {str(e)}")
