"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.core_handlers.job_queue
- RESPONSIBILITY: Proxy UI interactions for the Job Queue.
- CALLED BY: app.core.desktop.logic.core_handlers.__init__ (as Mixin)
- CALLS TO: app.core.desktop.logic.job_queue.ui_manager.JobQueueUIManager
- IN = OUT: Instantiates JobQueueUIManager lazily and forwards context menu events.
=============================================================================
"""

class JobQueueHandlersMixin:
    @property
    def job_queue_ui_manager(self):
        if not hasattr(self, '_job_queue_ui_manager_obj'):
            from app.core.desktop.logic.job_queue.ui_manager import JobQueueUIManager
            self._job_queue_ui_manager_obj = JobQueueUIManager(self)
        return self._job_queue_ui_manager_obj

    def _show_queue_context_menu(self, position):
        return self.job_queue_ui_manager.show_queue_context_menu(position)

    def _resume_selected_jobs(self):
        return self.job_queue_ui_manager.resume_selected_jobs()

    def _restart_selected_jobs(self):
        return self.job_queue_ui_manager.restart_selected_jobs()

    def _show_history_context_menu(self, position):
        return self.job_queue_ui_manager.show_history_context_menu(position)
