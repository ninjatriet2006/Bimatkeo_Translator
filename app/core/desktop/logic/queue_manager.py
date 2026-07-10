import os
import shutil
from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt, QObject

class QueueManager(QObject):
    def __init__(self, main_window):
        super().__init__()
        self.main_window = main_window
        
    def show_queue_context_menu(self, position):
        selected_items = self.main_window.queue_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        
        resume_action = menu.addAction("▶️ Resume (Bỏ qua file đã hoàn thành)")
        resume_action.triggered.connect(self.resume_selected_jobs)
        
        restart_action = menu.addAction("🔄 Restart (Dịch lại từ đầu)")
        restart_action.triggered.connect(self.restart_selected_jobs)

        menu.addSeparator()
        if hasattr(self.main_window, '_duplicate_selected_jobs'):
            duplicate_action = menu.addAction("➕ Duplicate Job (as new task)")
            duplicate_action.triggered.connect(self.main_window._duplicate_selected_jobs)

        if hasattr(self.main_window, '_remove_selected_jobs_from_queue'):
            remove_action = menu.addAction("🗑️ Remove from Queue")
            remove_action.triggered.connect(self.main_window._remove_selected_jobs_from_queue)

        menu.exec(self.main_window.queue_list_widget.mapToGlobal(position))

    def resume_selected_jobs(self):
        if hasattr(self.main_window, '_start_pipeline_thread'):
            self.main_window._start_pipeline_thread()
        
    def restart_selected_jobs(self):
        selected_items = self.main_window.queue_list_widget.selectedItems()
        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job = next((j for j in self.main_window.job_queue if j['id'] == job_id), None)
            if job:
                out_path = job.get('output_path', '')
                if os.path.exists(out_path):
                    try:
                        shutil.rmtree(out_path)
                    except Exception as e:
                        print(f"Lỗi xóa output_path {out_path}: {e}")
        if hasattr(self.main_window, '_start_pipeline_thread'):
            self.main_window._start_pipeline_thread()

    def show_history_context_menu(self, position):
        selected_items = self.main_window.history_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        if hasattr(self.main_window, '_requeue_job'):
            requeue_action = menu.addAction("↪️ Re-queue Job")
            requeue_action.triggered.connect(self.main_window._requeue_job)
        menu.exec(self.main_window.history_list_widget.mapToGlobal(position))
