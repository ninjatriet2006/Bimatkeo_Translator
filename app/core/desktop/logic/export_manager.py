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

    def _get_str(self, key, default):
        if hasattr(self.mw, 'get_string'):
            val = self.mw.get_string(key)
            if val != key:
                return val
        return default

    def export_detector_image(self):
        title_err = self._get_str("ui_export_error", "Export Error")
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            msg = self._get_str("ui_msg_no_test_results", "No test results available to export. Please run a test first.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        source_file = os.path.join(self.mw.current_test_output_dir, "test_detector.png")
        if not os.path.exists(source_file):
            msg = self._get_str("ui_msg_det_not_found", "Detector result image not found.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        title_dlg = self._get_str("ui_dlg_export_detector", "Export Detector Image")
        save_path, _ = QFileDialog.getSaveFileName(self.mw, title_dlg, "detector_result.png", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                title_suc = self._get_str("ui_success", "Success")
                msg_suc = self._get_str("ui_msg_det_exported", "Detector image exported successfully.")
                QMessageBox.information(self.mw, title_suc, msg_suc)
            except Exception as e:
                title_fail = self._get_str("ui_error", "Error")
                msg_fail = self._get_str("ui_msg_export_failed", "Failed to export image: {err}").format(err=str(e))
                QMessageBox.critical(self.mw, title_fail, msg_fail)

    def export_ocr_data(self):
        title_err = self._get_str("ui_export_error", "Export Error")
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            msg = self._get_str("ui_msg_no_test_results", "No test results available to export. Please run a test first.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        source_file = os.path.join(self.mw.current_test_output_dir, "test_data.json")
        if not os.path.exists(source_file):
            msg = self._get_str("ui_msg_ocr_not_found", "OCR data not found.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        title_dlg = self._get_str("ui_dlg_export_ocr", "Export OCR Data")
        save_path, _ = QFileDialog.getSaveFileName(self.mw, title_dlg, "ocr_data.csv", "CSV Files (*.csv)")
        if save_path:
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                bboxes = data.get("bboxes", [])
                original_texts = data.get("original_texts", [])
                
                with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    col1 = self._get_str("ui_col_bbox", "BBox")
                    col2 = self._get_str("ui_col_orig_text", "Original Text")
                    writer.writerow([col1, col2])
                    for i in range(max(len(bboxes), len(original_texts))):
                        box = str(bboxes[i]) if i < len(bboxes) else ""
                        text = original_texts[i] if i < len(original_texts) else ""
                        writer.writerow([box, text])
                title_suc = self._get_str("ui_success", "Success")
                msg_suc = self._get_str("ui_msg_ocr_exported", "OCR data exported successfully.")
                QMessageBox.information(self.mw, title_suc, msg_suc)
            except Exception as e:
                title_fail = self._get_str("ui_error", "Error")
                msg_fail = self._get_str("ui_msg_export_failed_ocr", "Failed to export OCR data: {err}").format(err=str(e))
                QMessageBox.critical(self.mw, title_fail, msg_fail)

    def export_translator_data(self):
        title_err = self._get_str("ui_export_error", "Export Error")
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            msg = self._get_str("ui_msg_no_test_results", "No test results available to export. Please run a test first.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        source_file = os.path.join(self.mw.current_test_output_dir, "test_data.json")
        if not os.path.exists(source_file):
            msg = self._get_str("ui_msg_trans_not_found", "Translation data not found.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        title_dlg = self._get_str("ui_dlg_export_trans", "Export Translated Text")
        save_path, _ = QFileDialog.getSaveFileName(self.mw, title_dlg, "translated_text.csv", "CSV Files (*.csv)")
        if save_path:
            try:
                with open(source_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                original_texts = data.get("original_texts", [])
                translated_texts = data.get("translated_texts", [])
                
                with open(save_path, 'w', newline='', encoding='utf-8-sig') as f:
                    writer = csv.writer(f)
                    col1 = self._get_str("ui_col_orig_text", "Original Text")
                    col2 = self._get_str("ui_col_trans_text", "Translated Text")
                    writer.writerow([col1, col2])
                    for i in range(max(len(original_texts), len(translated_texts))):
                        orig = original_texts[i] if i < len(original_texts) else ""
                        trans = translated_texts[i] if i < len(translated_texts) else ""
                        writer.writerow([orig, trans])
                title_suc = self._get_str("ui_success", "Success")
                msg_suc = self._get_str("ui_msg_trans_exported", "Translated text exported successfully.")
                QMessageBox.information(self.mw, title_suc, msg_suc)
            except Exception as e:
                title_fail = self._get_str("ui_error", "Error")
                msg_fail = self._get_str("ui_msg_export_failed_trans", "Failed to export translated text: {err}").format(err=str(e))
                QMessageBox.critical(self.mw, title_fail, msg_fail)

    def export_inpainter_image(self):
        title_err = self._get_str("ui_export_error", "Export Error")
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            msg = self._get_str("ui_msg_no_test_results", "No test results available to export. Please run a test first.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        source_file = os.path.join(self.mw.current_test_output_dir, "test_inpainter.png")
        if not os.path.exists(source_file):
            msg = self._get_str("ui_msg_inp_not_found", "Inpainter result image not found.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        title_dlg = self._get_str("ui_dlg_export_inp", "Export Inpainted Image")
        save_path, _ = QFileDialog.getSaveFileName(self.mw, title_dlg, "inpainter_result.png", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                title_suc = self._get_str("ui_success", "Success")
                msg_suc = self._get_str("ui_msg_inp_exported", "Inpainted image exported successfully.")
                QMessageBox.information(self.mw, title_suc, msg_suc)
            except Exception as e:
                title_fail = self._get_str("ui_error", "Error")
                msg_fail = self._get_str("ui_msg_export_failed", "Failed to export image: {err}").format(err=str(e))
                QMessageBox.critical(self.mw, title_fail, msg_fail)

    def export_render_image(self):
        title_err = self._get_str("ui_export_error", "Export Error")
        if not hasattr(self.mw, 'current_test_output_dir') or not self.mw.current_test_output_dir:
            msg = self._get_str("ui_msg_no_test_results", "No test results available to export. Please run a test first.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        if not hasattr(self.mw, 'test_image_path') or not self.mw.test_image_path:
            msg = self._get_str("ui_msg_no_test_img", "No test image path found.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        original_filename = os.path.basename(self.mw.test_image_path)
        output_filename = os.path.splitext(original_filename)[0] + ".png"
        source_file = os.path.join(self.mw.current_test_output_dir, output_filename)
        
        if not os.path.exists(source_file):
            msg = self._get_str("ui_msg_ren_not_found", "Render result image not found.")
            QMessageBox.warning(self.mw, title_err, msg)
            return
            
        title_dlg = self._get_str("ui_dlg_export_ren", "Export Rendered Image")
        save_path, _ = QFileDialog.getSaveFileName(self.mw, title_dlg, f"{output_filename}", "Images (*.png)")
        if save_path:
            try:
                shutil.copy2(source_file, save_path)
                title_suc = self._get_str("ui_success", "Success")
                msg_suc = self._get_str("ui_msg_ren_exported", "Rendered image exported successfully.")
                QMessageBox.information(self.mw, title_suc, msg_suc)
            except Exception as e:
                title_fail = self._get_str("ui_error", "Error")
                msg_fail = self._get_str("ui_msg_export_failed", "Failed to export image: {err}").format(err=str(e))
                QMessageBox.critical(self.mw, title_fail, msg_fail)
