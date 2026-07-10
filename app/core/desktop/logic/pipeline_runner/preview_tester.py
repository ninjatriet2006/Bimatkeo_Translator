"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.pipeline_runner.preview_tester
- RESPONSIBILITY: Run a translation preview on a single page.
- CALLED BY: app.core.desktop.logic.job_runner
- CALLS TO: app.core.desktop.logic.pipeline_runner.process_worker
- IN = OUT: Generates a translated image for preview display.
=============================================================================
"""
import os
import shutil
import threading
import copy
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QFileDialog, QMessageBox, QGraphicsView, QTableWidgetItem
from PySide6.QtCore import Qt, QTimer

class PreviewTester:
    def __init__(self, main_window):
        self.mw = main_window

    def load_test_image(self):
        file_path, _ = QFileDialog.getOpenFileName(self.mw, "Select a Test Image", "", "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not file_path:
            return

        self.mw.test_image_path = file_path
        print(f"[Visual Test] Loaded test image: {os.path.basename(file_path)}")

        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                raise ValueError("Pixmap is null. The image file may be corrupt or in an unsupported format.")

            if hasattr(self.mw, 'scene_detector'):
                if getattr(self.mw, 'item_detector', None):
                    self.mw.scene_detector.removeItem(self.mw.item_detector)
                self.mw.scene_detector.clear()
                self.mw.item_detector = self.mw.scene_detector.addPixmap(pixmap)

            for attr_name, scene in [('item_inpainter', getattr(self.mw, 'scene_inpainter', None)), 
                                     ('item_render', getattr(self.mw, 'scene_render', None))]:
                if scene is not None:
                    item = getattr(self.mw, attr_name, None)
                    if item:
                        scene.removeItem(item)
                    scene.clear()
                    setattr(self.mw, attr_name, None)

            if hasattr(self.mw, 'run_test_button'):
                self.mw.run_test_button.setEnabled(True)
            QTimer.singleShot(50, self.fit_image_to_view)

        except Exception as e:
            print(f"[ERROR] Failed to load image file: {e}")
            QMessageBox.critical(self.mw, "Error", f"Could not load the image:\n{e}")

    def fit_image_to_view(self):
        for view, scene, item_attr in [
            (getattr(self.mw, 'view_detector', None), getattr(self.mw, 'scene_detector', None), 'item_detector'),
            (getattr(self.mw, 'view_inpainter', None), getattr(self.mw, 'scene_inpainter', None), 'item_inpainter'),
            (getattr(self.mw, 'view_render', None), getattr(self.mw, 'scene_render', None), 'item_render')
        ]:
            if view and scene and getattr(self.mw, item_attr, None):
                view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self.update_zoom_label()

    def wheel_event_zoom(self, event):
        views = [getattr(self.mw, 'view_detector', None), getattr(self.mw, 'view_inpainter', None), getattr(self.mw, 'view_render', None)]
        views = [v for v in views if v is not None]
        
        if not views or event.modifiers() != Qt.KeyboardModifier.ControlModifier:
            for v in views:
                if v and v.underMouse():
                    QGraphicsView.wheelEvent(v, event)
            return

        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        current_zoom = views[0].transform().m11()

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        if hasattr(self.mw, 'limit_zoom_check') and self.mw.limit_zoom_check.isChecked():
            min_zoom, max_zoom = 0.05, 8.0
            if (current_zoom * zoom_factor > min_zoom
                    and current_zoom * zoom_factor < max_zoom):
                for v in views:
                    v.scale(zoom_factor, zoom_factor)
        else:
            min_zoom, max_zoom = 0.01, 100.0
            if (current_zoom * zoom_factor > min_zoom
                    and current_zoom * zoom_factor < max_zoom):
                for v in views:
                    v.scale(zoom_factor, zoom_factor)

        self.update_zoom_label()

    def update_zoom_label(self):
        view = getattr(self.mw, 'view_detector', None)
        if view and hasattr(self.mw, 'zoom_label'):
            zoom = view.transform().m11()
            self.mw.zoom_label.setText(f"Zoom: {zoom * 100:.0f}%")

    def run_visual_test_thread(self):
        if not getattr(self.mw, 'test_image_path', None):
            QMessageBox.warning(self.mw, "No Image", "Please load a test image first.")
            return

        settings = self.mw.current_settings
        translator_type = settings.get("translator_category", "offline")
        
        if translator_type == "offline":
            offline_model = settings.get("offline_translator", "none")
            if not offline_model or offline_model == "none" or offline_model.startswith("---"):
                QMessageBox.warning(self.mw, "Lỗi Thiết Lập", "Vui lòng chọn Offline Model trước khi bắt đầu (Không thể để là --- Select ---).")
                return
        else:
            ai_mode = settings.get("ai_mode", "")
            if ai_mode == "pool":
                pool_name = settings.get("pool_name", "")
                if not pool_name or pool_name.startswith("---"):
                    QMessageBox.warning(self.mw, "Lỗi Thiết Lập", "Vui lòng chọn Pool trước khi bắt đầu.")
                    return
            else:
                ai_model = settings.get("ai_model") or settings.get("api_name")
                if not ai_model or ai_model == "none" or ai_model.startswith("---"):
                    QMessageBox.warning(self.mw, "Lỗi Thiết Lập", "Vui lòng chọn AI Model trước khi bắt đầu.")
                    return

        missing = self.mw.config_loader.missing_required_fields(settings)
        if missing:
            names = ", ".join(self.mw.config_loader.full_config_data.get(f, {}).get("label", f.replace("_", " ").title()) for f in missing)
            QMessageBox.critical(
                self.mw,
                "Thiếu mô hình bắt buộc",
                "Không thể chạy Test. Các mô hình bắt buộc chưa được cài đặt:\n\n"
                f"  - {names}\n\n"
                "Hãy cài đặt mô hình cho các mục này (hoặc chọn mô hình khả dụng) rồi thử lại."
            )
            return

        test_job = {
            "id": "visual_test_job",
            "job_type": "T",
            "settings": copy.deepcopy(self.mw.current_settings)
        }

        if hasattr(self.mw, 'fast_preview_check') and self.mw.fast_preview_check.isChecked():
            self.mw.log("INFO", "Fast Preview enabled. Overriding settings for speed.")
            test_job['settings'].update({'detection_size': 1024, 'inpainting_size': 1024})
            if test_job['settings'].get('processing_device') == 'cuda':
                test_job['settings']['inpainting_precision'] = 'bf16'

        try:
            final_config = self.mw.thread_manager.build_final_config_for_job(test_job)
        except ValueError as e:
            QMessageBox.warning(self.mw, "Configuration Error", str(e))
            return

        if hasattr(self.mw, 'run_test_button'):
            self.mw.run_test_button.setEnabled(False)
            self.mw.run_test_button.setText("Testing...")

        thread = threading.Thread(target=self.run_visual_test, args=(test_job, final_config,), daemon=True)
        thread.start()

    def run_visual_test(self, test_job, final_config):
        try:
            self.mw.log("PIPELINE", "Starting visual test pipeline...")

            source_dir = os.path.dirname(self.mw.test_image_path)
            source_name = os.path.splitext(os.path.basename(self.mw.test_image_path))[0]
            final_output_dir = os.path.join(source_dir, f"{source_name}_translated_test")

            if os.path.exists(final_output_dir):
                shutil.rmtree(final_output_dir)

            is_verbose = test_job['settings'].get("enable_verbose_output", False)

            success = self.mw.process_worker.run_pipeline_in_process(
                self.mw.test_image_path,
                final_output_dir,
                final_config,
                is_verbose,
                "png",
                is_single_test=True
            )

            if success:
                self.mw.log("SUCCESS", "Visual test backend process completed.")
                if hasattr(self.mw, 'visual_test_result_signal'):
                    self.mw.visual_test_result_signal.emit(final_output_dir)
            else:
                self.mw.log("ERROR", "Visual test failed or was stopped.")
                if os.path.exists(final_output_dir) and not os.listdir(final_output_dir):
                    shutil.rmtree(final_output_dir)

        except Exception as e:
            self.mw.log("ERROR", f"Exception during visual test: {e}")
        finally:
            if hasattr(self.mw, 'visual_test_finished_signal'):
                self.mw.visual_test_finished_signal.emit()

    def display_test_result(self, output_dir: str):
        import json
        
        self.mw.current_test_output_dir = output_dir
        self.mw.log("INFO", f"Đang hiển thị kết quả từ: {output_dir}")
        try:
            det_path = os.path.join(output_dir, "test_detector.png")
            if os.path.exists(det_path):
                if getattr(self.mw, 'item_detector', None):
                    self.mw.scene_detector.removeItem(self.mw.item_detector)
                self.mw.scene_detector.clear()
                self.mw.item_detector = self.mw.scene_detector.addPixmap(QPixmap(det_path))
                
            inp_path = os.path.join(output_dir, "test_inpainter.png")
            if os.path.exists(inp_path):
                if getattr(self.mw, 'item_inpainter', None):
                    self.mw.scene_inpainter.removeItem(self.mw.item_inpainter)
                self.mw.scene_inpainter.clear()
                self.mw.item_inpainter = self.mw.scene_inpainter.addPixmap(QPixmap(inp_path))
                
            if hasattr(self.mw, 'test_image_path'):
                original_filename = os.path.basename(self.mw.test_image_path)
                output_filename = os.path.splitext(original_filename)[0] + ".png"
                ren_path = os.path.join(output_dir, output_filename)
                if os.path.exists(ren_path):
                    if getattr(self.mw, 'item_render', None):
                        self.mw.scene_render.removeItem(self.mw.item_render)
                    self.mw.scene_render.clear()
                    self.mw.item_render = self.mw.scene_render.addPixmap(QPixmap(ren_path))
            
            json_path = os.path.join(output_dir, "test_data.json")
            if os.path.exists(json_path) and hasattr(self.mw, 'table_ocr') and hasattr(self.mw, 'table_translator'):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                bboxes = data.get("bboxes") or []
                original_texts = data.get("original_texts") or []
                translated_texts = data.get("translated_texts") or []
                
                self.mw.table_ocr.setRowCount(len(bboxes))
                for i in range(len(bboxes)):
                    box_str = str(bboxes[i]) if i < len(bboxes) else ""
                    orig_str = original_texts[i] if i < len(original_texts) else ""
                    
                    item_box = QTableWidgetItem(box_str)
                    item_orig = QTableWidgetItem(orig_str)
                    item_box.setFlags(item_box.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_orig.setFlags(item_orig.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    self.mw.table_ocr.setItem(i, 0, item_box)
                    self.mw.table_ocr.setItem(i, 1, item_orig)
                    
                self.mw.table_translator.setRowCount(len(original_texts))
                for i in range(len(original_texts)):
                    orig_str = original_texts[i] if i < len(original_texts) else ""
                    trans_str = translated_texts[i] if i < len(translated_texts) else ""
                    
                    item_orig = QTableWidgetItem(orig_str)
                    item_trans = QTableWidgetItem(trans_str)
                    item_orig.setFlags(item_orig.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    self.mw.table_translator.setItem(i, 0, item_orig)
                    self.mw.table_translator.setItem(i, 1, item_trans)
            
            self.fit_image_to_view()

        except Exception as e:
            self.mw.log("ERROR", f"Failed to load preview results: {e}")
            QMessageBox.critical(self.mw, "Error", f"Could not load the preview results:\n{e}")

    def on_visual_test_finished(self):
        if hasattr(self.mw, 'run_test_button'):
            self.mw.run_test_button.setEnabled(True)
            self.mw.run_test_button.setText("Run Test")
