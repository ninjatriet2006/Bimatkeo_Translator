"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.job_queue_manager
- RESPONSIBILITY: Decoupled job queue manager and context menu handler.
- CALLED BY: app.core.desktop.logic.core_handlers.job_queue, app.core.desktop.main_window
- CALLS TO: PySide6.QtWidgets, PySide6.QtCore
- IN = OUT: Primitive parameter project_base_dir into __init__, emits PySide6 Signals for events.
=============================================================================
"""
import os
import shutil
from PySide6.QtCore import QObject, Qt, Signal
from PySide6.QtWidgets import QMenu

class JobQueueUIManager(QObject):
    action_triggered = Signal(str, object)
    job_restart_requested = Signal(list)
    job_resume_requested = Signal()

    def __init__(self, project_base_dir: str = "."):
        super().__init__()
        self.project_base_dir = project_base_dir

    def show_queue_context_menu(self, main_window, position):
        mw = main_window
        if not mw or not hasattr(mw, 'queue_list_widget'):
            return
        selected_items = mw.queue_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        
        get_str = getattr(mw, "get_string", lambda k: k)
        resume_text = get_str("ui_menu_resume") if get_str("ui_menu_resume") != "ui_menu_resume" else "▶️ Resume (Bỏ qua file đã hoàn thành)"
        resume_action = menu.addAction(resume_text)
        resume_action.triggered.connect(mw._resume_selected_jobs)
        
        restart_text = get_str("ui_menu_restart") if get_str("ui_menu_restart") != "ui_menu_restart" else "🔄 Restart (Dịch lại từ đầu)"
        restart_action = menu.addAction(restart_text)
        restart_action.triggered.connect(mw._restart_selected_jobs)

        menu.addSeparator()
        dup_text = get_str("ui_menu_duplicate") if get_str("ui_menu_duplicate") != "ui_menu_duplicate" else "➕ Duplicate Job (as new task)"
        duplicate_action = menu.addAction(dup_text)
        duplicate_action.triggered.connect(mw._duplicate_selected_jobs)

        rem_text = get_str("ui_menu_remove_queue") if get_str("ui_menu_remove_queue") != "ui_menu_remove_queue" else "🗑️ Remove from Queue"
        remove_action = menu.addAction(rem_text)
        remove_action.triggered.connect(mw._remove_selected_jobs_from_queue)

        menu.exec(mw.queue_list_widget.mapToGlobal(position))

    def resume_selected_jobs(self, main_window):
        if main_window and hasattr(main_window, '_start_pipeline_thread'):
            main_window._start_pipeline_thread()
        self.job_resume_requested.emit()
        
    def restart_selected_jobs(self, main_window):
        mw = main_window
        restarted_ids = []
        if mw and hasattr(mw, 'queue_list_widget'):
            selected_items = mw.queue_list_widget.selectedItems()
            for item in selected_items:
                job_id = item.data(Qt.ItemDataRole.UserRole)
                job = next((j for j in getattr(mw, 'job_queue', []) if j['id'] == job_id), None)
                if job:
                    out_path = job.get('output_path', '')
                    if os.path.exists(out_path):
                        try:
                            shutil.rmtree(out_path)
                        except Exception as e:
                            print(f"Lỗi xóa output_path {out_path}: {e}")
                    restarted_ids.append(job_id)
            if hasattr(mw, '_start_pipeline_thread'):
                mw._start_pipeline_thread()
        self.job_restart_requested.emit(restarted_ids)

    def show_history_context_menu(self, main_window, position):
        mw = main_window
        if not mw or not hasattr(mw, 'history_list_widget'):
            return
        selected_items = mw.history_list_widget.selectedItems()
        if not selected_items:
            return

        menu = QMenu()
        get_str = getattr(mw, "get_string", lambda k: k)
        req_text = get_str("ui_menu_requeue") if get_str("ui_menu_requeue") != "ui_menu_requeue" else "↪️ Re-queue Job"
        requeue_action = menu.addAction(req_text)
        requeue_action.triggered.connect(mw._requeue_job)
        menu.exec(mw.history_list_widget.mapToGlobal(position))


JobQueueManager = JobQueueUIManager

