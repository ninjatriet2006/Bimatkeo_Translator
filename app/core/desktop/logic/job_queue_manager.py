"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.job_queue_manager
- RESPONSIBILITY: Handle context menu logic for the job queue list.
- CALLED BY: app.core.desktop.logic.core_handlers.job_queue
- CALLS TO: PySide6.QtWidgets
- IN = OUT: Maps UI right-click events to file operations or clipboard actions.
=============================================================================
"""
import os
from PySide6.QtWidgets import QMenu
from PySide6.QtCore import Qt

class JobQueueUIManager:
    def __init__(self, main_window):
        self.mw = main_window

    def show_queue_context_menu(self, position):
        selected_items = self.mw.queue_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        
        resume_action = menu.addAction("▶️ Resume (Bỏ qua file đã hoàn thành)")
        resume_action.triggered.connect(self.mw._resume_selected_jobs)
        
        restart_action = menu.addAction("🔄 Restart (Dịch lại từ đầu)")
        restart_action.triggered.connect(self.mw._restart_selected_jobs)

        menu.addSeparator()
        duplicate_action = menu.addAction("➕ Duplicate Job (as new task)")
        duplicate_action.triggered.connect(self.mw._duplicate_selected_jobs)

        remove_action = menu.addAction("🗑️ Remove from Queue")
        remove_action.triggered.connect(self.mw._remove_selected_jobs_from_queue)

        menu.exec(self.mw.queue_list_widget.mapToGlobal(position))

    def resume_selected_jobs(self):
        self.mw._start_pipeline_thread()
        
    def restart_selected_jobs(self):
        import shutil
        selected_items = self.mw.queue_list_widget.selectedItems()
        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job = next((j for j in self.mw.job_queue if j['id'] == job_id), None)
            if job:
                out_path = job.get('output_path', '')
                if os.path.exists(out_path):
                    try:
                        shutil.rmtree(out_path)
                    except Exception as e:
                        print(f"Lỗi xóa output_path {out_path}: {e}")
        self.mw._start_pipeline_thread()

    def show_history_context_menu(self, position):
        selected_items = self.mw.history_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        requeue_action = menu.addAction("↪️ Re-queue Job")
        requeue_action.triggered.connect(self.mw._requeue_job)
        menu.exec(self.mw.history_list_widget.mapToGlobal(position))
