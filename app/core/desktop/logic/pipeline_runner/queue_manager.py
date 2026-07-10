import os
import copy
import time
from PySide6.QtWidgets import QFileDialog, QMessageBox, QListWidgetItem, QSlider
from PySide6.QtCore import Qt

class QueueManager:
    def __init__(self, main_window):
        self.mw = main_window

    def add_job(self):
        initial_dir = getattr(self.mw, 'last_selected_directory', self.mw.project_base_dir)
        folder_path = QFileDialog.getExistingDirectory(self.mw, "Select Manga/Image Folder", initial_dir)

        if folder_path:
            self.mw.last_selected_directory = folder_path
            self.add_job_from_path(folder_path)

    def add_file_job(self):
        initial_dir = getattr(self.mw, 'last_selected_directory', self.mw.project_base_dir)
        file_paths, _ = QFileDialog.getOpenFileNames(self.mw, "Select Image or Text Files", initial_dir, "Supported Files (*.png *.jpg *.jpeg *.webp *.bmp *.txt);;Text Files (*.txt);;Image Files (*.png *.jpg *.jpeg *.webp *.bmp);;All Files (*)")

        if file_paths:
            self.mw.last_selected_directory = os.path.dirname(file_paths[0])
            for path in file_paths:
                self.add_job_from_path(path)

    def add_job_from_path(self, path):
        job_id = f"job_{int(time.time() * 1000)}_{len(self.mw.job_queue)}"
        job_data = {
            "id": job_id,
            "source_path": path,
            "name": os.path.basename(path),
            "settings": copy.deepcopy(self.mw.current_settings),
            "status": "Ready",
            "job_type": "T"
        }
        self.mw.job_queue.append(job_data)

        self.update_job_list_ui()

        for i in range(self.mw.queue_list_widget.count()):
            item = self.mw.queue_list_widget.item(i)
            if item.data(Qt.ItemDataRole.UserRole) == job_id:
                self.mw.queue_list_widget.setCurrentRow(i)
                break

    def duplicate_selected_jobs(self):
        selected_items = self.mw.queue_list_widget.selectedItems()
        if not selected_items:
            return

        jobs_to_add = []
        for item in selected_items:
            original_job_id = item.data(Qt.ItemDataRole.UserRole)
            original_job = next((job for job in self.mw.job_queue if job['id'] == original_job_id), None)

            if original_job:
                new_job = {
                    "id": f"job_{int(time.time() * 1000)}_{len(self.mw.job_queue) + len(jobs_to_add)}",
                    "source_path": original_job['source_path'],
                    "name": original_job['name'],
                    "settings": copy.deepcopy(original_job.get('settings', self.mw.current_settings)),
                    "status": "Ready",
                    "job_type": "T"
                }
                jobs_to_add.append(new_job)

        self.mw.job_queue.extend(jobs_to_add)
        self.update_job_list_ui()
        self.mw.log("INFO", f"Duplicated {len(jobs_to_add)} job(s).")

    def clear_list_data(self, data_list, name: str, update_ui_func):
        if not data_list:
            return

        reply = QMessageBox.question(self.mw, f"Confirm Clear {name}",
                                     f"Are you sure you want to remove ALL jobs from the {name.lower()}?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                                     QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            data_list.clear()
            self.mw.log("INFO", f"{name} has been cleared.")
            update_ui_func()

    def clear_queue(self):
        self.clear_list_data(self.mw.job_queue, "Queue", self.update_job_list_ui)

    def clear_history(self):
        self.clear_list_data(self.mw.history_queue, "History", self.update_history_list_ui)

    def move_job(self, direction: str):
        if not getattr(self.mw, 'selected_job_id', None) or len(self.mw.job_queue) < 2:
            return

        index = self.get_selected_job_index()
        if index is None:
            return

        if direction == "up" and index > 0:
            new_index = index - 1
        elif direction == "down" and index < len(self.mw.job_queue) - 1:
            new_index = index + 1
        else:
            return

        self.mw.job_queue.insert(new_index, self.mw.job_queue.pop(index))
        self.update_job_list_ui()
        self.mw.queue_list_widget.setCurrentRow(new_index)

    def update_job_list_ui(self):
        self.mw.queue_list_widget.blockSignals(True)
        self.mw.queue_list_widget.clear()

        for i, job in enumerate(self.mw.job_queue, 1):
            status_icon = "⚪"
            if job.get('status') == "Ready":
                status_icon = "🟢"
            elif job.get('status') == "Processing":
                status_icon = "🟡"

            job_type = job.get('job_type')
            job_type_tag = f"[{job_type}]" if job_type else ""

            display_text = f"{i}. {job_type_tag} {status_icon} {job['name']}"
            item = QListWidgetItem(display_text)
            
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            check_state = Qt.Checked if job.get('status') == 'Ready' else Qt.Unchecked
            item.setCheckState(check_state)
            
            item.setData(Qt.ItemDataRole.UserRole, job['id'])
            self.mw.queue_list_widget.addItem(item)

        self.mw.queue_list_widget.blockSignals(False)

    def on_queue_item_changed(self, item: QListWidgetItem):
        job_id = item.data(Qt.ItemDataRole.UserRole)
        job = next((j for j in self.mw.job_queue if j['id'] == job_id), None)
        if job:
            is_checked = item.checkState() == Qt.Checked
            job['status'] = 'Ready' if is_checked else 'Awaiting Config'

    def update_history_list_ui(self):
        self.mw.history_list_widget.clear()

        for i, job in enumerate(reversed(self.mw.history_queue), 1):
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

            self.mw.history_list_widget.addItem(item)

    def on_job_selection_changed(self):
        selected_items = self.mw.queue_list_widget.selectedItems()
        if not selected_items:
            self.mw.selected_job_id = None
        else:
            self.mw.selected_job_id = selected_items[0].data(Qt.ItemDataRole.UserRole)

    def populate_settings_panel(self):
        from PySide6.QtWidgets import QWidget
        job_index = self.get_selected_job_index()
        if job_index is not None:
            settings_source = self.mw.job_queue[job_index]['settings']
        else:
            settings_source = self.mw.current_settings
            if hasattr(self.mw.config_loader, 'app_language'):
                settings_source['app_language'] = self.mw.config_loader.app_language

        self.mw.current_settings = copy.deepcopy(settings_source)

        for widget in self.mw.setting_widgets.values():
            if widget:
                widget.blockSignals(True)
                if isinstance(widget, QWidget) and widget.findChild(QSlider):
                    widget.findChild(QSlider).blockSignals(True)

        for key, value in self.mw.current_settings.items():
            widget = self.mw.setting_widgets.get(key)
            if widget:
                if key == 'translator_chain':
                    if hasattr(self.mw, '_rebuild_chain_from_string'):
                        self.mw._rebuild_chain_from_string(value or "")
                    enable_checkbox = self.mw.setting_widgets.get('enable_translator_chain')
                    if enable_checkbox:
                        is_chain_enabled = bool(value)
                        enable_checkbox.setChecked(is_chain_enabled)
                        if hasattr(self.mw, '_update_chain_ui_state'):
                            self.mw._update_chain_ui_state()
                else:
                    self.mw._set_widget_value(key, value, widget)

        for widget in self.mw.setting_widgets.values():
            if widget:
                widget.blockSignals(False)
                if isinstance(widget, QWidget) and widget.findChild(QSlider):
                    widget.findChild(QSlider).blockSignals(False)
                    
        if hasattr(self.mw, '_update_translator_visibility'):
            self.mw._update_translator_visibility()
        target_lang_widget = self.mw.setting_widgets.get('target_lang')
        if target_lang_widget:
            if hasattr(self.mw, '_filter_translator_dropdowns'):
                self.mw._filter_translator_dropdowns(target_lang_widget.currentText())

    def get_selected_job_index(self) -> int | None:
        if not getattr(self.mw, 'selected_job_id', None):
            return None
        for i, job in enumerate(self.mw.job_queue):
            if job['id'] == self.mw.selected_job_id:
                return i
        return None

    def remove_selected_jobs_from_queue(self):
        selected_items = self.mw.queue_list_widget.selectedItems()
        if not selected_items:
            return

        ids_to_remove = {item.data(Qt.ItemDataRole.UserRole) for item in selected_items}

        self.mw.job_queue = [job for job in self.mw.job_queue if job['id'] not in ids_to_remove]

        self.mw.log("INFO", f"Removed {len(ids_to_remove)} job(s) from the queue.")
        if getattr(self.mw, 'selected_job_id', None) in ids_to_remove:
            self.mw.selected_job_id = None
            self.populate_settings_panel()

        self.update_job_list_ui()

    def requeue_job(self):
        selected_items = self.mw.history_list_widget.selectedItems()
        if not selected_items:
            return

        for item in reversed(selected_items):
            job_id_to_requeue = item.data(Qt.ItemDataRole.UserRole)
            job_to_move = next((job for job in self.mw.history_queue if job['id'] == job_id_to_requeue), None)

            if job_to_move:
                self.mw.history_queue.remove(job_to_move)
                job_to_move['status'] = 'Ready'
                self.mw.job_queue.append(job_to_move)

        self.update_history_list_ui()
        self.update_job_list_ui()
