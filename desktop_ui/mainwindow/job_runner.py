# type: ignore
# ===============================================================
# JobRunnerMixin - Queue and Pipeline Execution Handlers
#
# Author: User & Gemini Collaboration
# ===============================================================

import os
import sys
import shutil
import threading
import copy
import time
import multiprocessing
import queue
from PySide6.QtWidgets import QFileDialog, QMessageBox, QListWidgetItem, QApplication, QWidget, QSlider, QComboBox, QCheckBox, QLineEdit, QPushButton, QButtonGroup
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QPixmap, QColor
from PIL import Image

def _pipeline_process_worker(job_or_path, output_path, config_dict, is_verbose, output_format, log_queue, result_queue, hitl_tx_queue, hitl_rx_queue, temp_dir, python_exec, is_single_test=False):
    from app.core.pipeline import Pipeline
    import threading
    
    waiting_ctxs = {}
    
    def log_callback(level, message):
        log_queue.put((level, message))
        
    try:
        pipeline = Pipeline(None, python_exec, temp_dir)
        if is_single_test:
            success = pipeline.run_single_image_test(job_or_path, output_path, config_dict, log_callback, is_verbose)
        else:
            success = pipeline.run(job_or_path, output_path, config_dict, log_callback, is_verbose, output_format)
            
        result_queue.put({"success": success})
    except Exception as e:
        log_queue.put(("ERROR", f"Critical Process Error: {e}"))
        result_queue.put({"success": False})
    finally:
        hitl_rx_queue.put(None)

class JobRunnerMixin:
    def _add_job(self):
        """Opens a dialog to select a folder and adds it as a job."""
        initial_dir = getattr(self, 'last_selected_directory', self.project_base_dir)
        folder_path = QFileDialog.getExistingDirectory(self, "Select Manga/Image Folder", initial_dir)

        if folder_path:
            self.last_selected_directory = folder_path
            self._add_job_from_path(folder_path)

    def _add_file_job(self):
        """Opens a dialog to select files and adds them as jobs."""
        initial_dir = getattr(self, 'last_selected_directory', self.project_base_dir)
        file_paths, _ = QFileDialog.getOpenFileNames(self, "Select Image or Text Files", initial_dir, "Supported Files (*.png *.jpg *.jpeg *.webp *.bmp *.txt);;Text Files (*.txt);;Image Files (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*)")

        if file_paths:
            self.last_selected_directory = os.path.dirname(file_paths[0])
            for path in file_paths:
                self._add_job_from_path(path)

    def _add_job_from_path(self, path):
        """
        Adds a job with a default '''Awaiting Config''' status to the queue
        and selects it in the UI.
        """
        job_id = f"job_{int(time.time() * 1000)}_{len(self.job_queue)}"
        job_data = {
            "id": job_id,
            "source_path": path,
            "name": os.path.basename(path),
            "settings": copy.deepcopy(self.current_settings),
            "status": "Ready",
            "job_type": "T"
        }
        self.job_queue.append(job_data)

        self._update_job_list_ui()

        for i in range(self.queue_list_widget.count()):
            item = self.queue_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == job_id:
                self.queue_list_widget.setCurrentRow(i)
                break

    def dragEnterEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dragMoveEvent(self, event):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()

    def dropEvent(self, event):
        if event.mimeData().hasUrls():
            for url in event.mimeData().urls():
                path = url.toLocalFile()
                if os.path.isdir(path):
                    self._add_job_from_path(path)
                else:
                    self.log("WARNING", f"Dropped item is not a directory: {path}")
            event.acceptProposedAction()
        else:
            event.ignore()

    def _duplicate_selected_jobs(self):
        """
        Creates a new job using the same source path and settings as the selected job(s).
        """
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        jobs_to_add = []
        for item in selected_items:
            original_job_id = item.data(Qt.ItemDataRole.UserRole)
            original_job = next((job for job in self.job_queue if job['id'] == original_job_id), None)

            if original_job:
                new_job = {
                    "id": f"job_{int(time.time() * 1000)}_{len(self.job_queue) + len(jobs_to_add)}",
                    "source_path": original_job['source_path'],
                    "name": original_job['name'],
                    "settings": copy.deepcopy(original_job.get('settings', self.current_settings)),
                    "status": "Ready",
                    "job_type": "T"
                }
                jobs_to_add.append(new_job)

        self.job_queue.extend(jobs_to_add)
        self._update_job_list_ui()
        self.log("INFO", f"Duplicated {len(jobs_to_add)} job(s).")

    def _clear_list_data(self, data_list, name: str, update_ui_func):
        if not data_list:
            return

        reply = QMessageBox.question(self, f"Confirm Clear {name}",
                                     f"Are you sure you want to remove ALL jobs from the {name.lower()}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            data_list.clear()
            self.log("INFO", f"{name} has been cleared.")
            update_ui_func()

    def _clear_queue(self):
        """Removes all jobs from the queue after confirmation."""
        self._clear_list_data(self.job_queue, "Queue", self._update_job_list_ui)

    def _clear_history(self):
        """Removes all jobs from the history list after confirmation."""
        self._clear_list_data(self.history_queue, "History", self._update_history_list_ui)

    def _move_job(self, direction: str):
        """Moves the selected job up or down in the queue."""
        if not self.selected_job_id or len(self.job_queue) < 2:
            return

        index = self._get_selected_job_index()
        if index is None:
            return

        if direction == "up" and index > 0:
            new_index = index - 1
        elif direction == "down" and index < len(self.job_queue) - 1:
            new_index = index + 1
        else:
            return

        self.job_queue.insert(new_index, self.job_queue.pop(index))
        self._update_job_list_ui()
        self.queue_list_widget.setCurrentRow(new_index)

    def _update_job_list_ui(self):
        """
        Refreshes both the queue and history list widgets based on the current state
        of self.job_queue and self.history_queue.
        """
        self.queue_list_widget.blockSignals(True)
        self.queue_list_widget.clear()

        for i, job in enumerate(self.job_queue, 1):
            status_icon = "⚪"
            if job.get('status') == "Ready":
                status_icon = "🟢"
            elif job.get('status') == "Processing":
                status_icon = "🟡"

            job_type = job.get('job_type')
            job_type_tag = f"[{job_type}]" if job_type else ""

            display_text = f"{i}. {job_type_tag} {status_icon} {job['name']}"
            item = QListWidgetItem(display_text)
            
            # Enable checkbox
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            check_state = Qt.Checked if job.get('status') == 'Ready' else Qt.Unchecked
            item.setCheckState(check_state)
            
            item.setData(Qt.ItemDataRole.UserRole, job['id'])
            self.queue_list_widget.addItem(item)

        self.queue_list_widget.blockSignals(False)

    def _on_queue_item_changed(self, item: QListWidgetItem):
        """Called when a user checks/unchecks an item in the queue."""
        job_id = item.data(Qt.ItemDataRole.UserRole)
        job = next((j for j in self.job_queue if j['id'] == job_id), None)
        if job:
            is_checked = item.checkState() == Qt.Checked
            job['status'] = 'Ready' if is_checked else 'Awaiting Config'


    def _update_history_list_ui(self):
        """Refreshes the history list widget based on the self.history_queue."""
        self.history_list_widget.clear()

        for i, job in enumerate(reversed(self.history_queue), 1):
            status = job.get('status', 'Unknown')

            if status == "Completed":
                status_icon = "✅"
            elif status == "Failed":
                status_icon = "❌"
            elif status == "Stopped":
                status_icon = "⏹️"
            else:
                status_icon = "❔"

            job_type = job.get('job_type')
            job_type_tag = f"[{job_type}]" if job_type else ""

            display_text = f"{i}. {job_type_tag} {status_icon} {job['name']}"

            item = QListWidgetItem(display_text)
            item.setData(Qt.ItemDataRole.UserRole, job['id'])

            if status == "Failed" or status == "Stopped":
                item.setForeground(Qt.GlobalColor.red)
            elif status == "Completed":
                item.setForeground(Qt.GlobalColor.green)

            self.history_list_widget.addItem(item)

    def _on_job_selection_changed(self):
        """
        Handles the logic when a different job is selected in the queue list.
        This now ONLY updates the internal reference to the selected job ID
        and no longer automatically loads its settings into the panel.
        """
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            self.selected_job_id = None
        else:
            self.selected_job_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

        print(f"[Jobs] Selection changed to job ID: {self.selected_job_id}. Panel state is not affected.")

    def _populate_settings_panel(self):
        """
        Updates all setting widgets to reflect the settings of the currently selected job
        OR the application's default settings if no job is selected.
        This function is now smart enough to handle special compound widgets.
        """
        job_index = self._get_selected_job_index()
        if job_index is not None:
            settings_source = self.job_queue[job_index]['settings']
        else:
            settings_source = self.current_settings
            if hasattr(self.config_loader, 'app_language'):
                settings_source['app_language'] = self.config_loader.app_language

        self.current_settings = copy.deepcopy(settings_source)

        for widget in self.setting_widgets.values():
            if widget:
                widget.blockSignals(True)
                if isinstance(widget, QWidget) and widget.findChild(QSlider):
                    widget.findChild(QSlider).blockSignals(True)

        for key, value in self.current_settings.items():
            widget = self.setting_widgets.get(key)
            if widget:
                if key == '''translator_chain''':
                    if hasattr(self, '''_rebuild_chain_from_string'''):
                        self._rebuild_chain_from_string(value or "")
                    enable_checkbox = self.setting_widgets.get('''enable_translator_chain''')
                    if enable_checkbox:
                        is_chain_enabled = bool(value)
                        enable_checkbox.setChecked(is_chain_enabled)
                        self._update_chain_ui_state()
                else:
                    self._set_widget_value(key, value, widget)

        for widget in self.setting_widgets.values():
            if widget:
                widget.blockSignals(False)
                if isinstance(widget, QWidget) and widget.findChild(QSlider):
                    widget.findChild(QSlider).blockSignals(False)
                    
        self._update_translator_visibility()
        target_lang_widget = self.setting_widgets.get('''target_lang''')
        if target_lang_widget:
            self._filter_translator_dropdowns(target_lang_widget.currentText())

    def _get_selected_job_index(self) -> int | None:
        """Finds the index in job_queue for the currently selected job_id."""
        if not self.selected_job_id:
            return None
        for i, job in enumerate(self.job_queue):
            if job['id'] == self.selected_job_id:
                return i
        return None

    def _load_test_image(self):
        """Opens a file dialog to load a test image and displays it."""
        from PySide6.QtGui import QPixmap
        from PySide6.QtWidgets import QFileDialog, QMessageBox
        
        file_path, _ = QFileDialog.getOpenFileName(self, "Select a Test Image", "", "Image Files (*.png *.jpg *.jpeg *.webp *.bmp)")
        if not file_path:
            return

        self.test_image_path = file_path
        print(f"[Visual Test] Loaded test image: {os.path.basename(file_path)}")

        try:
            pixmap = QPixmap(file_path)
            if pixmap.isNull():
                raise ValueError("Pixmap is null. The image file may be corrupt or in an unsupported format.")

            # Load the original image into the detector view as a preview
            if hasattr(self, 'scene_detector'):
                if getattr(self, 'item_detector', None):
                    self.scene_detector.removeItem(self.item_detector)
                self.scene_detector.clear()
                self.item_detector = self.scene_detector.addPixmap(pixmap)

            # Clear other scenes
            for attr_name, scene in [('item_inpainter', getattr(self, 'scene_inpainter', None)), 
                                     ('item_render', getattr(self, 'scene_render', None))]:
                if scene is not None:
                    item = getattr(self, attr_name, None)
                    if item:
                        scene.removeItem(item)
                    scene.clear()
                    setattr(self, attr_name, None)

            self.run_test_button.setEnabled(True)
            QTimer.singleShot(50, self._fit_image_to_view)

        except Exception as e:
            print(f"[ERROR] Failed to load image file: {e}")
            QMessageBox.critical(self, "Error", f"Could not load the image:\n{e}")

    def _fit_image_to_view(self):
        """Resets the view to fit the entire image within the visible area."""
        from PySide6.QtCore import Qt
        for view, scene, item_attr in [
            (getattr(self, 'view_detector', None), getattr(self, 'scene_detector', None), 'item_detector'),
            (getattr(self, 'view_inpainter', None), getattr(self, 'scene_inpainter', None), 'item_inpainter'),
            (getattr(self, 'view_render', None), getattr(self, 'scene_render', None), 'item_render')
        ]:
            if view and scene and getattr(self, item_attr, None):
                view.fitInView(scene.sceneRect(), Qt.AspectRatioMode.KeepAspectRatio)
        self._update_zoom_label()

    def _wheel_event_zoom(self, event):
        """Handles zooming with Ctrl+MouseWheel, respecting the zoom limit checkbox."""
        from PySide6.QtWidgets import QGraphicsView
        from PySide6.QtCore import Qt
        
        # Check if the event source is one of our views
        views = [getattr(self, 'view_detector', None), getattr(self, 'view_inpainter', None), getattr(self, 'view_render', None)]
        views = [v for v in views if v is not None]
        
        if not views or event.modifiers() != Qt.KeyboardModifier.ControlModifier:
            for v in views:
                if v and v.underMouse():
                    QGraphicsView.wheelEvent(v, event)
            return

        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Use the first valid view as reference for current zoom
        current_zoom = views[0].transform().m11()

        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor

        if self.limit_zoom_check.isChecked():
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

        self._update_zoom_label()

    def _update_zoom_label(self):
        """Updates the zoom level display label."""
        view = getattr(self, 'view_detector', None)
        if view:
            zoom = view.transform().m11()
            self.zoom_label.setText(f"Zoom: {zoom * 100:.0f}%")

    def _run_visual_test_thread(self):
        """Starts the visual test pipeline in a separate thread to avoid freezing the UI."""
        if not self.test_image_path:
            QMessageBox.warning(self, "No Image", "Please load a test image first.")
            return

        settings = self.current_settings
        translator_type = settings.get("translator_category", "Offline")
        
        if translator_type == "Offline":
            offline_model = settings.get("offline_translator", "none")
            if not offline_model or offline_model == "none" or offline_model.startswith("---"):
                QMessageBox.warning(self, "Lỗi Thiết Lập", "Vui lòng chọn Offline Model trước khi bắt đầu (Không thể để là --- Select ---).")
                return
        else:
            ai_mode = settings.get("ai_mode", "")
            if ai_mode == "Pool APIs":
                pool_name = settings.get("pool_name", "")
                if not pool_name or pool_name.startswith("---"):
                    QMessageBox.warning(self, "Lỗi Thiết Lập", "Vui lòng chọn Pool trước khi bắt đầu.")
                    return
            else:
                ai_model = settings.get("ai_model") or settings.get("api_name")
                if not ai_model or ai_model == "none" or ai_model.startswith("---"):
                    QMessageBox.warning(self, "Lỗi Thiết Lập", "Vui lòng chọn AI Model trước khi bắt đầu.")
                    return

        missing = self.config_loader.missing_required_fields(settings)
        if missing:
            names = ", ".join(self.config_loader.full_config_data.get(f, {}).get("label", f.replace("_", " ").title()) for f in missing)
            QMessageBox.critical(
                self,
                "Thiếu mô hình bắt buộc",
                "Không thể chạy Test. Các mô hình bắt buộc chưa được cài đặt:\n\n"
                f"  - {names}\n\n"
                "Hãy cài đặt mô hình cho các mục này (hoặc chọn mô hình khả dụng) rồi thử lại."
            )
            return

        test_job = {
            "id": "visual_test_job",
            "job_type": "T",
            "settings": copy.deepcopy(self.current_settings)
        }

        if self.fast_preview_check.isChecked():
            self.log("INFO", "Fast Preview enabled. Overriding settings for speed.")
            test_job['settings'].update({'detection_size': 1024, 'inpainting_size': 1024})
            if test_job['settings'].get('processing_device') == 'NVIDIA GPU':
                test_job['settings']['inpainting_precision'] = 'bf16'

        try:
            final_config = self._build_final_config_for_job(test_job)
        except ValueError as e:
            QMessageBox.warning(self, "Configuration Error", str(e))
            return

        self.run_test_button.setEnabled(False)
        self.run_test_button.setText("Testing...")

        thread = threading.Thread(target=self._run_visual_test, args=(test_job, final_config,), daemon=True)
        thread.start()

    def _run_visual_test(self, test_job, final_config):
        """Prepares and runs the pipeline on the single loaded test image."""
        try:
            self.log("PIPELINE", "Starting visual test pipeline...")

            source_dir = os.path.dirname(self.test_image_path)
            source_name = os.path.splitext(os.path.basename(self.test_image_path))[0]
            final_output_dir = os.path.join(source_dir, f"{source_name}_translated_test")

            if os.path.exists(final_output_dir):
                shutil.rmtree(final_output_dir)

            is_verbose = test_job['settings'].get("enable_verbose_output", False)

            success = self._run_pipeline_in_process(
                self.test_image_path,
                final_output_dir,
                final_config,
                is_verbose,
                "png",
                is_single_test=True
            )

            if success:
                self.log("SUCCESS", "Visual test backend process completed.")
                if hasattr(self, 'visual_test_result_signal'):
                    self.visual_test_result_signal.emit(final_output_dir)
            else:
                self.log("ERROR", "Visual test failed or was stopped.")
                if os.path.exists(final_output_dir) and not os.listdir(final_output_dir):
                    shutil.rmtree(final_output_dir)

        except Exception as e:
            self.log("ERROR", f"Exception during visual test: {e}")
        finally:
            if hasattr(self, 'visual_test_finished_signal'):
                self.visual_test_finished_signal.emit()

    def _display_test_result(self, output_dir: str):
        """Loads the intermediate results and displays them in the Preview Tester sub-tabs."""
        import json
        from PySide6.QtWidgets import QTableWidgetItem
        from PySide6.QtCore import Qt
        
        self.current_test_output_dir = output_dir
        self.log("INFO", f"Đang hiển thị kết quả từ: {output_dir}")
        try:
            # 1. Detector
            det_path = os.path.join(output_dir, "test_detector.png")
            if os.path.exists(det_path):
                if getattr(self, 'item_detector', None):
                    self.scene_detector.removeItem(self.item_detector)
                self.scene_detector.clear()
                self.item_detector = self.scene_detector.addPixmap(QPixmap(det_path))
                
            # 2. Inpainter
            inp_path = os.path.join(output_dir, "test_inpainter.png")
            if os.path.exists(inp_path):
                if getattr(self, 'item_inpainter', None):
                    self.scene_inpainter.removeItem(self.item_inpainter)
                self.scene_inpainter.clear()
                self.item_inpainter = self.scene_inpainter.addPixmap(QPixmap(inp_path))
                
            # 3. Render Output
            if hasattr(self, 'test_image_path'):
                original_filename = os.path.basename(self.test_image_path)
                output_filename = os.path.splitext(original_filename)[0] + ".png"
                ren_path = os.path.join(output_dir, output_filename)
                if os.path.exists(ren_path):
                    if getattr(self, 'item_render', None):
                        self.scene_render.removeItem(self.item_render)
                    self.scene_render.clear()
                    self.item_render = self.scene_render.addPixmap(QPixmap(ren_path))
            
            # 4. Text Data (OCR and Translator)
            json_path = os.path.join(output_dir, "test_data.json")
            if os.path.exists(json_path):
                with open(json_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    
                bboxes = data.get("bboxes", [])
                original_texts = data.get("original_texts", [])
                translated_texts = data.get("translated_texts", [])
                
                # Update OCR Table
                self.table_ocr.setRowCount(len(bboxes))
                for i in range(len(bboxes)):
                    box_str = str(bboxes[i]) if i < len(bboxes) else ""
                    orig_str = original_texts[i] if i < len(original_texts) else ""
                    
                    item_box = QTableWidgetItem(box_str)
                    item_orig = QTableWidgetItem(orig_str)
                    item_box.setFlags(item_box.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    item_orig.setFlags(item_orig.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    self.table_ocr.setItem(i, 0, item_box)
                    self.table_ocr.setItem(i, 1, item_orig)
                    
                # Update Translator Table
                self.table_translator.setRowCount(len(original_texts))
                for i in range(len(original_texts)):
                    orig_str = original_texts[i] if i < len(original_texts) else ""
                    trans_str = translated_texts[i] if i < len(translated_texts) else ""
                    
                    item_orig = QTableWidgetItem(orig_str)
                    item_trans = QTableWidgetItem(trans_str)
                    item_orig.setFlags(item_orig.flags() & ~Qt.ItemFlag.ItemIsEditable)
                    
                    self.table_translator.setItem(i, 0, item_orig)
                    self.table_translator.setItem(i, 1, item_trans)
            
            self._fit_image_to_view()

        except Exception as e:
            self.log("ERROR", f"Failed to load preview results: {e}")
            QMessageBox.critical(self, "Error", f"Could not load the preview results:\n{e}")

    def _on_visual_test_finished(self):
        """Resets the '''Run Test''' button to its normal state."""
        self.run_test_button.setEnabled(True)
        self.run_test_button.setText("Run Test")

    def _start_pipeline_thread(self):
        """Starts the main job processing pipeline in a separate thread."""
        if self.is_running_pipeline:
            return
        if not self.job_queue:
            QMessageBox.information(self, "Information", "Please add one or more jobs to the queue first.")
            return

        for job in self.job_queue:
            if job.get('status') != 'Ready' or job.get('job_type') not in ['T', 'TX']:
                continue
            settings = self.current_settings
            translator_type = settings.get("translator_category", "Offline")
            
            if translator_type == "Offline":
                offline_model = settings.get("offline_translator", "none")
                if not offline_model or offline_model == "none" or offline_model.startswith("---"):
                    QMessageBox.warning(self, "Lỗi Thiết Lập", f"Job '{job.get('name')}': Vui lòng chọn Offline Model trước khi bắt đầu (Không thể để là --- Select ---).")
                    return
            else:
                ai_mode = settings.get("ai_mode", "")
                if ai_mode == "Pool APIs":
                    pool_name = settings.get("pool_name", "")
                    if not pool_name or pool_name.startswith("---"):
                        QMessageBox.warning(self, "Lỗi Thiết Lập", f"Job '{job.get('name')}': Vui lòng chọn Pool trước khi bắt đầu.")
                        return
                else:
                    ai_model = settings.get("ai_model") or settings.get("api_name")
                    if not ai_model or ai_model == "none" or ai_model.startswith("---"):
                        QMessageBox.warning(self, "Lỗi Thiết Lập", f"Job '{job.get('name')}': Vui lòng chọn AI Model trước khi bắt đầu.")
                        return

        # Block the run if any REQUIRED model field (detector,
        # ocr, inpainter) is blank or not set up in the global settings.
        # We validate against self.current_settings because _build_final_config_for_job
        # uses global settings as the single source of truth.
        blocked = []
        global_missing = self.config_loader.missing_required_fields(self.current_settings)

        for job in self.job_queue:
            if job.get('status') != 'Ready':
                continue
            if job.get('job_type') == 'TX':
                continue
            if global_missing:
                names = ", ".join(self.config_loader.full_config_data.get(f, {}).get("label", f.replace("_", " ").title()) for f in global_missing)
                blocked.append((job.get('id', '?'), names))

        if blocked:
            lines = "\n".join(f"  - Job {jid}: {names}" for jid, names in blocked)
            QMessageBox.critical(
                self,
                "Thiếu mô hình bắt buộc",
                "Không thể chạy. Các job sau có mô hình bắt buộc chưa được cài đặt "
                "(detector / OCR / inpainter):\n\n"
                f"{lines}\n\n"
                "Hãy cài đặt mô hình cho các mục này (hoặc chọn mô hình khả dụng) rồi thử lại."
            )
            return

        self._stopped_by_user = False
        self._toggle_ui_state(True)
        thread = threading.Thread(target=self._run_pipeline, daemon=True)
        thread.start()

    def _update_colorize_restore_ui_state(self):
        """Enables or disables the upscale factor widget based on the checkbox."""
        restore_checkbox = self.setting_widgets.get('restore_size_after_colorize')
        factor_widget = self.setting_widgets.get('colorize_upscale_factor')

        if not all([restore_checkbox, factor_widget]):
            return

        is_enabled = restore_checkbox.isChecked()
        factor_widget.setEnabled(is_enabled)

    def _build_final_config_for_job(self, job: dict) -> dict:
        """
        Builds the correct, nested config dictionary for a specific job
        by ONLY using the global current_settings object.
        """
        job_type = job.get('job_type')
        settings = self.current_settings
        
        final_config = {}
        all_props = self.config_loader.full_config_data

        for key, prop_info in all_props.items():
            if key not in settings: continue
            
            value = settings.get(key)
            if value == "" or value is None: continue
            
            if key == 'font_family':
                continue

            group = prop_info.get("group", "")
            translator_keys = ["processing_device", "translator_category", "api_name", "offline_translator", "ai_translator", "ai_endpoint", "ai_model", "ai_key", "max_retries", "enable_translator_chain", "translator_chain", "target_lang", "no_text_lang_skip", "skip_lang", "system_prompt_profile", "max_request_length"]
            if key in translator_keys:
                target_dict = final_config.setdefault("translator", {})
            elif key in ["ocr", "merge_nearby_boxes", "min_text_length", "ignore_bubble", "prob", "filter_text"]:
                target_dict = final_config.setdefault("ocr", {})
            elif key in ["detector", "detection_size", "text_threshold", "det_rotate", 
                         "det_auto_rotate", "det_invert", "det_gamma_correct", "box_threshold", "unclip_ratio"]:
                target_dict = final_config.setdefault("detector", {})

            elif key in ["inpainter", "inpainting_precision", "inpainting_size"] or "Image & Inpainter" in group:
                target_dict = final_config.setdefault("inpainter", {})
            elif "Render & Output" in group:
                target_dict = final_config.setdefault("render", {})
            else:
                final_config[key] = value
                continue
            
            target_dict[key] = value

        selected_font_name = settings.get('font_family')
        if selected_font_name and selected_font_name in self.font_map:
            final_config['font_path'] = self.font_map[selected_font_name]
            final_config.setdefault('render', {})['gimp_font'] = selected_font_name

        translator_dict = final_config.setdefault("translator", {})
        category = settings.get('translator_category', 'Offline')
        if category == 'Offline':
            translator_dict['translator'] = settings.get('offline_translator', 'none')
        else:
            ai_mode = settings.get('ai_mode', 'Standalone API')
            if ai_mode == 'Pool APIs':
                pool_name = settings.get('pool_name', '')
                translator_dict['translator'] = 'pool'
                translator_dict['pool_name'] = pool_name
                translator_dict['pool_apis'] = []
                
                if hasattr(self, '_load_pool_profiles') and hasattr(self, '_load_api_profiles'):
                    pools = self._load_pool_profiles()
                    api_profiles = self._load_api_profiles()
                    if pool_name in pools:
                        for api_name in pools[pool_name]:
                            prof = api_profiles.get(api_name, {})
                            if prof:
                                endpoint = prof.get('endpoint', '')
                                provider = prof.get('provider')
                                if not provider:
                                    from app.core.api_utils import infer_ai_provider
                                    provider = infer_ai_provider(endpoint)
                                    
                                translator_dict['pool_apis'].append({
                                    'translator': provider,
                                    'endpoint': prof.get('endpoint', ''),
                                    'model': prof.get('model', ''),
                                    'api_key': prof.get('key', '')
                                })
            else:
                provider = settings.get('ai_translator')
                api_name = settings.get('api_name')
                
                if api_name and api_name != 'none':
                    if hasattr(self, '_load_api_profiles'):
                        api_profiles = self._load_api_profiles()
                        prof = api_profiles.get(api_name, {})
                        if prof:
                            provider = prof.get('provider')
                            translator_dict['ai_endpoint'] = prof.get('endpoint', '')
                            translator_dict['ai_model'] = prof.get('model', '')
                            translator_dict['ai_api_key'] = prof.get('key', '')
                
                from app.core.api_utils import infer_ai_provider
                ep = translator_dict.get('ai_endpoint', '')
                if ep:
                    inferred = infer_ai_provider(ep)
                    if inferred and provider != inferred:
                        provider = inferred
                
                if not provider or provider == 'none':
                    provider = 'openai'
                    
                translator_dict['translator'] = provider

        # --- Handle OCR API Profiles ---
        ocr_category = settings.get('ocr_category', 'Offline')
        if ocr_category == 'AI / Online':
            ocr_ai_mode = settings.get('ocr_ai_mode', 'Standalone API')
            if ocr_ai_mode == 'Pool APIs':
                pool_name = settings.get('ocr_pool_name', '')
                final_config['api_ocr'] = 'pool'
                final_config['api_ocr_pool'] = []
                if hasattr(self, '_load_pool_profiles') and hasattr(self, '_load_api_profiles'):
                    pools = self._load_pool_profiles("OCR")
                    api_profiles = self._load_api_profiles()
                    if pool_name in pools:
                        for api_name in pools[pool_name]:
                            prof = api_profiles.get(api_name, {})
                            if prof:
                                final_config['api_ocr_pool'].append({
                                    'translator': prof.get('provider', ''),
                                    'endpoint': prof.get('endpoint', ''),
                                    'model': prof.get('model', ''),
                                    'api_key': prof.get('key', '')
                                })
            else:
                ocr_api_name = settings.get('ocr_api_name')
                if ocr_api_name and ocr_api_name != 'none':
                    if hasattr(self, '_load_api_profiles'):
                        api_profiles = self._load_api_profiles()
                        prof = api_profiles.get(ocr_api_name, {})
                        if prof:
                            final_config['api_ocr'] = prof.get('provider', settings.get('api_ocr'))
                            final_config['api_ocr_key'] = prof.get('key', '')

        if settings.get('translator_chain'):
            final_config.get("translator", {}).pop('translator', None)
        
        final_config['processing_device'] = settings.get('processing_device', 'CPU')


        if job_type == 'TX':
            final_config['pipeline'] = {
                "enable_ocr": False,
                "enable_translator": True,
                "enable_inpainter": False,
                "enable_renderer": False
            }
            
        final_config['job_type'] = job_type

        return final_config

    def _run_pipeline_in_process(self, job_or_path, output_path, config_dict, is_verbose, output_format, is_single_test=False):
        log_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
        hitl_tx_queue = multiprocessing.Queue()
        self.hitl_rx_queue = multiprocessing.Queue()
        
        self.current_process = multiprocessing.Process(
            target=_pipeline_process_worker,
            args=(job_or_path, output_path, config_dict, is_verbose, output_format, log_queue, result_queue, hitl_tx_queue, self.hitl_rx_queue, self.temp_dir, self.config_loader.python_executable, is_single_test)
        )
        self.current_process.start()
        
        success = False
        while self.current_process.is_alive():
            while True:
                try:
                    level, msg = log_queue.get_nowait()
                    self.log(level, msg)
                except queue.Empty:
                    break
                    
            if self._stopped_by_user:
                self.current_process.terminate()
                self.current_process.join()
                self.log("PIPELINE", "Process terminated by user.")
                return False
                
            time.sleep(0.1)
            QApplication.processEvents()
            
        while True:
            try:
                level, msg = log_queue.get_nowait()
                self.log(level, msg)
            except queue.Empty:
                break
                
        try:
            result = result_queue.get_nowait()
            success = result.get("success", False)
        except queue.Empty:
            if self.current_process.exitcode != 0 and not self._stopped_by_user:
                self.log("ERROR", f"Process crashed unexpectedly! Exit code: {self.current_process.exitcode}")
            success = False
            
        self.current_process = None
        return success

    def _run_pipeline(self):
        """
        Processes all '''Ready''' jobs in the queue sequentially.
        """
        try:
            while self.is_running_pipeline:
                job_to_process = next((job for job in self.job_queue if job.get('status') == 'Ready'), None)
                if not job_to_process:
                    self.log("PIPELINE", "No more '''Ready''' jobs in the queue. Finishing run.")
                    break

                job = job_to_process
                self.currently_processing_job_id = job['id']
                job['status'] = 'Processing'
                self._update_job_list_ui()
                self._toggle_ui_state(True, job['id'])

                settings = self.current_settings
                selected_mode = settings.get('processing_mode', 'Automatic')
                output_format = settings.get('output_format', 'png')

                mode_to_use = 'High VRAM'
                if selected_mode == 'Low VRAM' or (selected_mode == 'Automatic' and self.detected_vram_gb > 0 and self.detected_vram_gb <= 6):
                    mode_to_use = 'Low VRAM'

                source_path = job['source_path']
                job_type_tag = f"TASK-{job.get('job_type')}" if job.get('job_type') != 'T' else settings.get('target_lang', 'ENG')
                base_output_folder_name = f"{os.path.basename(source_path)}-{job_type_tag}"
                output_dir = os.path.dirname(source_path)
                
                final_output_folder_name = base_output_folder_name

                if os.path.isfile(source_path):
                    final_output_path = output_dir
                    all_source_files = [os.path.basename(source_path)]
                    files_to_process = all_source_files
                else:
                    export_mode = settings.get('export_mode', 'Create New Folder (Avoid Overwrite)')
                    
                    if export_mode == 'Translate In-Place (Modify Original)':
                        final_output_path = source_path
                    else:
                        if export_mode == 'Create New Folder (Avoid Overwrite)':
                            counter = 1
                            while os.path.exists(os.path.join(output_dir, final_output_folder_name)):
                                final_output_folder_name = f"{base_output_folder_name} ({counter})"
                                counter += 1
                        elif export_mode == 'Create New Folder (Overwrite Existing)':
                            target_path = os.path.join(output_dir, final_output_folder_name)
                            if os.path.exists(target_path):
                                try:
                                    shutil.rmtree(target_path)
                                    self.log("INFO", f"Deleted existing output folder for overwrite: {target_path}")
                                except Exception as e:
                                    self.log("ERROR", f"Failed to delete existing output folder: {e}")
                        
                        final_output_path = os.path.join(output_dir, final_output_folder_name)
                        os.makedirs(final_output_path, exist_ok=True)
                        
                    all_source_files = sorted([f for f in os.listdir(source_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.txt'))])

                    try:
                        processed_files = {os.path.splitext(f)[0] for f in os.listdir(final_output_path) if f.lower().endswith(f".{output_format}") or f.lower().endswith('.txt')}
                        files_to_process = [f for f in all_source_files if os.path.splitext(f)[0] not in processed_files]
                    except FileNotFoundError:
                        files_to_process = all_source_files

                if not files_to_process:
                    self.log("INFO", f"All files for job '{job['name']}' seem to be processed already. Skipping to avoid errors.")
                    job['status'] = "Completed"
                    self.job_queue.remove(job)
                    self.history_queue.append(job)
                    self._update_job_list_ui()
                    self._update_history_list_ui()
                    QApplication.processEvents() 
                    continue

                self.log("INFO", f"Found {len(files_to_process)} unprocessed image(s) for job '''{job['name']}'''.")

                success = True
                if mode_to_use == 'Low VRAM':
                    # Legacy: Low VRAM Mode used to artificially batch images.
                    # Since the pipeline is concurrent and processes sequentially, VRAM peak is constant.
                    # We now run it identically to Fast Mode to preserve translation context windows.
                    self.log("PIPELINE", f"Resuming job '''{job['name']}''' in Low VRAM Mode (Sequential Stream).")
                    
                    final_config = self._build_final_config_for_job(job)
                    final_config['is_single_file'] = os.path.isfile(source_path)
                    is_verbose = settings.get("enable_verbose_output", False)
                    success = self._run_pipeline_in_process(job, final_output_path, final_config, is_verbose, output_format, is_single_test=False)
                else:
                    self.log("PIPELINE", f"Resuming job '''{job['name']}''' in High VRAM Mode.")

                    temp_source_dir = os.path.join(self.temp_dir, "high_vram_processing")
                    if os.path.exists(temp_source_dir): shutil.rmtree(temp_source_dir)
                    os.makedirs(temp_source_dir)
                    for f in files_to_process:
                        src_file = source_path if os.path.isfile(source_path) else os.path.join(source_path, f)
                        shutil.copy(src_file, temp_source_dir)

                    job_for_run = copy.deepcopy(job)
                    job_for_run['source_path'] = temp_source_dir

                    final_config = self._build_final_config_for_job(job_for_run)
                    final_config['is_single_file'] = os.path.isfile(source_path)
                    is_verbose = settings.get("enable_verbose_output", False)
                    success = self._run_pipeline_in_process(job_for_run, final_output_path, final_config, is_verbose, output_format, is_single_test=False)
                    shutil.rmtree(temp_source_dir)

                job['status'] = "Completed" if success else ("Stopped" if self._stopped_by_user else "Failed")

                if not success and not self._stopped_by_user:
                    QTimer.singleShot(0, lambda j=job: QMessageBox.critical(self, "Job Failed", f"The job '''{j['name']}''' failed due to a critical error.\n\nCheck the Live Log for details."))

                self.job_queue.remove(job)
                self.history_queue.append(job)
                self.currently_processing_job_id = None
                self._update_job_list_ui()
                self._update_history_list_ui()

                if self._stopped_by_user:
                    self.log("PIPELINE", "Pipeline stopped by user command.")
                    break
        finally:
            self.pipeline_finished_signal.emit()

    def _stop_pipeline(self):
        """Stops the running pipeline process immediately and updates the UI."""
        if not self.is_running_pipeline:
            return

        self.log("PIPELINE", "Stop command received. Terminating backend process...")
        self._stopped_by_user = True
        
        if hasattr(self, 'current_process') and self.current_process and self.current_process.is_alive():
            self.current_process.terminate()

    def _toggle_ui_state(self, is_running: bool, running_job_id: str = None):
        """
        Locks ONLY the essential UI elements during processing.
        """
        self.is_running_pipeline = is_running
        self.start_button.setEnabled(not is_running)
        self.stop_button.setEnabled(is_running)

        for i in range(self.queue_list_widget.count()):
            item = self.queue_list_widget.item(i)
            if is_running and item.data(Qt.ItemDataRole.UserRole) == running_job_id:
                item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
            else:
                item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)

    def _set_settings_panel_enabled(self, is_enabled: bool):
        """Helper function to enable or disable all widgets in the settings panel."""
        interactive_widget_types = (QPushButton, QComboBox, QCheckBox, QSlider, QLineEdit)

        if hasattr(self, '''settings_tab_view'''):
            for widget_type in interactive_widget_types:
                for widget in self.settings_tab_view.findChildren(widget_type):
                    widget.setEnabled(is_enabled)

    def _update_progress(self, percent: float, text: str):
        """Thread-safe method to update the progress bar and label."""
        self.progress_bar.setValue(int(percent * 100))
        self.progress_label.setText(text)



    def _on_pipeline_finished(self):
        """
        A dedicated, thread-safe function to call when the pipeline finishes.
        This centralizes the UI reset logic.
        """
        self.is_running_pipeline = False
        self.currently_processing_job_id = None
        self._update_progress(1.0, "Finished!")
        QTimer.singleShot(100, lambda: self._toggle_ui_state(False))
        QTimer.singleShot(2000, lambda: self._update_progress(0, "Ready"))

    def _apply_settings_to_selection(self):
        """Applies the main configuration from the '''Configuration''' tabs to the selected jobs."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job_data = next((job for job in self.job_queue if job['id'] == job_id), None)
            if job_data:
                job_data['settings'] = self.current_settings.copy()
                job_data['status'] = '''Ready'''
                job_data['job_type'] = '''T'''

        self.log("INFO", f"Applied '''Translate [T]''' settings to {len(selected_items)} job(s).")
        self._update_job_list_ui()

    def _remove_selected_jobs_from_queue(self):
        """Removes all selected jobs from the queue."""
        selected_items = self.queue_list_widget.selectedItems()
        if not selected_items:
            return

        ids_to_remove = {item.data(Qt.ItemDataRole.UserRole) for item in selected_items}

        self.job_queue = [job for job in self.job_queue if job['id'] not in ids_to_remove]

        self.log("INFO", f"Removed {len(ids_to_remove)} job(s) from the queue.")
        if self.selected_job_id in ids_to_remove:
            self.selected_job_id = None
            self._populate_settings_panel()

        self._update_job_list_ui()

    def _requeue_job(self):
        """Moves the selected job(s) from the history back to the queue for another run."""
        selected_items = self.history_list_widget.selectedItems()
        if not selected_items:
            return

        for item in reversed(selected_items):
            job_id_to_requeue = item.data(Qt.ItemDataRole.UserRole)
            job_to_move = next((job for job in self.history_queue if job['id'] == job_id_to_requeue), None)

            if job_to_move:
                self.history_queue.remove(job_to_move)
                job_to_move['status'] = '''Ready'''
                self.job_queue.append(job_to_move)

        self._update_history_list_ui()
        self._update_job_list_ui()

        self.log("INFO", f"Re-queued {len(selected_items)} job(s) from history.")
