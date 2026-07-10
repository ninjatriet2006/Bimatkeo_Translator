from app.core.desktop.logic.pipeline_runner.drag_drop_handler import DragDropHandler
from app.core.desktop.logic.pipeline_runner.queue_manager import QueueManager
from app.core.desktop.logic.pipeline_runner.thread_manager import ThreadManager
from app.core.desktop.logic.pipeline_runner.process_worker import ProcessWorker
from app.core.desktop.logic.pipeline_runner.preview_tester import PreviewTester

class JobRunnerMixin:
    @property
    def drag_drop_handler(self):
        if not hasattr(self, '_drag_drop_handler_obj'):
            self._drag_drop_handler_obj = DragDropHandler(self)
        return self._drag_drop_handler_obj

    @property
    def queue_manager(self):
        if not hasattr(self, '_queue_manager_obj'):
            self._queue_manager_obj = QueueManager(self)
        return self._queue_manager_obj

    @property
    def thread_manager(self):
        if not hasattr(self, '_thread_manager_obj'):
            self._thread_manager_obj = ThreadManager(self)
        return self._thread_manager_obj

    @property
    def process_worker(self):
        if not hasattr(self, '_process_worker_obj'):
            self._process_worker_obj = ProcessWorker(self)
        return self._process_worker_obj

    @property
    def preview_tester(self):
        if not hasattr(self, '_preview_tester_obj'):
            self._preview_tester_obj = PreviewTester(self)
        return self._preview_tester_obj

    # --- Drag & Drop ---
    def dragEnterEvent(self, event):
        return self.drag_drop_handler.dragEnterEvent(event)

    def dragMoveEvent(self, event):
        return self.drag_drop_handler.dragMoveEvent(event)

    def dropEvent(self, event):
        return self.drag_drop_handler.dropEvent(event)

    # --- Queue Manager ---
    def _add_job(self):
        return self.queue_manager.add_job()

    def _add_file_job(self):
        return self.queue_manager.add_file_job()

    def _add_job_from_path(self, path):
        return self.queue_manager.add_job_from_path(path)

    def _duplicate_selected_jobs(self):
        return self.queue_manager.duplicate_selected_jobs()

    def _clear_list_data(self, data_list, name: str, update_ui_func):
        return self.queue_manager.clear_list_data(data_list, name, update_ui_func)

    def _clear_queue(self):
        return self.queue_manager.clear_queue()

    def _clear_history(self):
        return self.queue_manager.clear_history()

    def _move_job(self, direction: str):
        return self.queue_manager.move_job(direction)

    def _update_job_list_ui(self):
        return self.queue_manager.update_job_list_ui()

    def _on_queue_item_changed(self, item):
        return self.queue_manager.on_queue_item_changed(item)

    def _update_history_list_ui(self):
        return self.queue_manager.update_history_list_ui()

    def _on_job_selection_changed(self):
        return self.queue_manager.on_job_selection_changed()

    def _populate_settings_panel(self):
        return self.queue_manager.populate_settings_panel()

    def _get_selected_job_index(self) -> int | None:
        return self.queue_manager.get_selected_job_index()

    def _remove_selected_jobs_from_queue(self):
        return self.queue_manager.remove_selected_jobs_from_queue()

    def _requeue_job(self):
        return self.queue_manager.requeue_job()

    # --- Thread Manager ---
    def _start_pipeline_thread(self):
        return self.thread_manager.start_pipeline_thread()

    def _update_colorize_restore_ui_state(self):
        return self.thread_manager.update_colorize_restore_ui_state()

    def _build_final_config_for_job(self, job: dict) -> dict:
        return self.thread_manager.build_final_config_for_job(job)

    def _run_pipeline(self):
        return self.thread_manager.run_pipeline()

    def _stop_pipeline(self):
        return self.thread_manager.stop_pipeline()

    def _toggle_ui_state(self, is_running: bool, running_job_id: str = None):
        return self.thread_manager.toggle_ui_state(is_running, running_job_id)

    def _set_settings_panel_enabled(self, is_enabled: bool):
        return self.thread_manager.set_settings_panel_enabled(is_enabled)

    def _update_progress(self, percent: float, text: str):
        return self.thread_manager.update_progress(percent, text)

    def _on_pipeline_finished(self):
        return self.thread_manager.on_pipeline_finished()

    def _apply_settings_to_selection(self):
        return self.thread_manager.apply_settings_to_selection()

    # --- Preview Tester ---
    def _load_test_image(self):
        return self.preview_tester.load_test_image()

    def _fit_image_to_view(self):
        return self.preview_tester.fit_image_to_view()

    def _wheel_event_zoom(self, event):
        return self.preview_tester.wheel_event_zoom(event)

    def _update_zoom_label(self):
        return self.preview_tester.update_zoom_label()

    def _run_visual_test_thread(self):
        return self.preview_tester.run_visual_test_thread()

    def _run_visual_test(self, test_job, final_config):
        return self.preview_tester.run_visual_test(test_job, final_config)

    def _display_test_result(self, output_dir: str):
        return self.preview_tester.display_test_result(output_dir)

    def _on_visual_test_finished(self):
        return self.preview_tester.on_visual_test_finished()
