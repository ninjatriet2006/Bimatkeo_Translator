"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.pipeline_runner.thread_manager
- RESPONSIBILITY: Manage translation threads and background processes.
- CALLED BY: app.core.desktop.logic.job_runner
- CALLS TO: app.core.desktop.logic.pipeline_runner.process_worker
- IN = OUT: Dispatches tasks to worker threads/processes.
=============================================================================
"""
import os
import shutil
import threading
from PySide6.QtWidgets import QMessageBox, QApplication, QPushButton, QComboBox, QCheckBox, QSlider, QLineEdit
from PySide6.QtCore import Qt, QTimer

class ThreadManager:
    def __init__(self, main_window):
        self.mw = main_window

    def start_pipeline_thread(self):
        if getattr(self.mw, 'is_running_pipeline', False):
            return
        if not getattr(self.mw, 'job_queue', []):
            QMessageBox.information(self.mw, "Information", "Please add one or more jobs to the queue first.")
            return

        for job in self.mw.job_queue:
            if job.get('status') != 'Ready' or job.get('job_type') not in ['T', 'TX']:
                continue
            settings = self.mw.current_settings
            translator_type = settings.get("translator_category", "offline")
            
            if translator_type == "offline":
                offline_model = settings.get("offline_translator", "none")
                if not offline_model or offline_model == "none" or offline_model.startswith("---"):
                    QMessageBox.warning(self.mw, "Lỗi Thiết Lập", f"Job '{job.get('name')}': Vui lòng chọn Offline Model trước khi bắt đầu (Không thể để là --- Select ---).")
                    return
            else:
                ai_mode = settings.get("ai_mode", "")
                if ai_mode == "pool":
                    pool_name = settings.get("pool_name", "")
                    if not pool_name or pool_name.startswith("---"):
                        QMessageBox.warning(self.mw, "Lỗi Thiết Lập", f"Job '{job.get('name')}': Vui lòng chọn Pool trước khi bắt đầu.")
                        return
                else:
                    ai_model = settings.get("ai_model") or settings.get("api_name")
                    if not ai_model or ai_model == "none" or ai_model.startswith("---"):
                        QMessageBox.warning(self.mw, "Lỗi Thiết Lập", f"Job '{job.get('name')}': Vui lòng chọn AI Model trước khi bắt đầu.")
                        return

        blocked = []
        global_missing = self.mw.config_loader.missing_required_fields(self.mw.current_settings)

        for job in self.mw.job_queue:
            if job.get('status') != 'Ready':
                continue
            if job.get('job_type') == 'TX':
                continue
            if global_missing:
                names = ", ".join(self.mw.config_loader.full_config_data.get(f, {}).get("label", f.replace("_", " ").title()) for f in global_missing)
                blocked.append((job.get('id', '?'), names))

        if blocked:
            lines = "\n".join(f"  - Job {jid}: {names}" for jid, names in blocked)
            QMessageBox.critical(
                self.mw,
                "Thiếu mô hình bắt buộc",
                "Không thể chạy. Các job sau có mô hình bắt buộc chưa được cài đặt "
                "(detector / OCR / inpainter):\n\n"
                f"{lines}\n\n"
                "Hãy cài đặt mô hình cho các mục này (hoặc chọn mô hình khả dụng) rồi thử lại."
            )
            return

        self.mw._stopped_by_user = False
        self.toggle_ui_state(True)
        thread = threading.Thread(target=self.run_pipeline, daemon=True)
        thread.start()

    def update_colorize_restore_ui_state(self):
        restore_checkbox = self.mw.setting_widgets.get('restore_size_after_colorize')
        factor_widget = self.mw.setting_widgets.get('colorize_upscale_factor')

        if not all([restore_checkbox, factor_widget]):
            return

        is_enabled = restore_checkbox.isChecked()
        factor_widget.setEnabled(is_enabled)

    def build_final_config_for_job(self, job: dict) -> dict:
        job_type = job.get('job_type')
        settings = self.mw.current_settings
        
        final_config = {}
        all_props = self.mw.config_loader.full_config_data

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
        if selected_font_name and selected_font_name in self.mw.font_map:
            final_config['font_path'] = self.mw.font_map[selected_font_name]
            final_config.setdefault('render', {})['gimp_font'] = selected_font_name

        translator_dict = final_config.setdefault("translator", {})
        category = settings.get('translator_category', 'offline')
        if category == 'offline':
            translator_dict['translator'] = settings.get('offline_translator', 'none')
        else:
            ai_mode = settings.get('ai_mode', 'standalone')
            if ai_mode == 'pool':
                pool_name = settings.get('pool_name', '')
                translator_dict['translator'] = 'pool'
                translator_dict['pool_name'] = pool_name
                translator_dict['pool_apis'] = []
                
                if hasattr(self.mw, '_load_pool_profiles') and hasattr(self.mw, '_load_api_profiles'):
                    pools = self.mw._load_pool_profiles()
                    api_profiles = self.mw._load_api_profiles()
                    if pool_name in pools:
                        for api_name in pools[pool_name]:
                            prof = api_profiles.get(api_name, {})
                            if prof:
                                endpoint = prof.get('endpoint', '')
                                provider = prof.get('provider')
                                if not provider:
                                    from app.core.api.manager import infer_ai_provider
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
                    if hasattr(self.mw, '_load_api_profiles'):
                        api_profiles = self.mw._load_api_profiles()
                        prof = api_profiles.get(api_name, {})
                        if prof:
                            provider = prof.get('provider')
                            translator_dict['ai_endpoint'] = prof.get('endpoint', '')
                            translator_dict['ai_model'] = prof.get('model', '')
                            translator_dict['ai_api_key'] = prof.get('key', '')
                
                from app.core.api.manager import infer_ai_provider
                ep = translator_dict.get('ai_endpoint', '')
                if ep:
                    inferred = infer_ai_provider(ep)
                    if inferred and provider != inferred:
                        provider = inferred
                
                if not provider or provider == 'none':
                    provider = 'openai'
                    
                translator_dict['translator'] = provider

        ocr_category = settings.get('ocr_category', 'offline')
        if ocr_category == 'api':
            ocr_ai_mode = settings.get('ocr_ai_mode', 'standalone')
            if ocr_ai_mode == 'pool':
                pool_name = settings.get('ocr_pool_name', '')
                final_config['api_ocr'] = 'pool'
                final_config['api_ocr_pool'] = []
                if hasattr(self.mw, '_load_pool_profiles') and hasattr(self.mw, '_load_api_profiles'):
                    pools = self.mw._load_pool_profiles("OCR")
                    api_profiles = self.mw._load_api_profiles()
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
                    if hasattr(self.mw, '_load_api_profiles'):
                        api_profiles = self.mw._load_api_profiles()
                        prof = api_profiles.get(ocr_api_name, {})
                        if prof:
                            final_config['api_ocr'] = prof.get('provider', settings.get('api_ocr'))
                            final_config['api_ocr_key'] = prof.get('key', '')

        if settings.get('translator_chain'):
            final_config.get("translator", {}).pop('translator', None)
        
        final_config['processing_device'] = settings.get('processing_device', 'cpu')


        if job_type == 'TX':
            final_config['pipeline'] = {
                "enable_ocr": False,
                "enable_translator": True,
                "enable_inpainter": False,
                "enable_renderer": False
            }
            
        final_config['job_type'] = job_type

        return final_config

    def run_pipeline(self):
        try:
            while getattr(self.mw, 'is_running_pipeline', False):
                job_to_process = next((job for job in self.mw.job_queue if job.get('status') == 'Ready'), None)
                if not job_to_process:
                    self.mw.log("PIPELINE", "No more 'Ready' jobs in the queue. Finishing run.")
                    break

                job = job_to_process
                self.mw.currently_processing_job_id = job['id']
                job['status'] = 'Processing'
                if hasattr(self.mw.queue_manager, 'update_job_list_ui'):
                    self.mw.queue_manager.update_job_list_ui()
                self.toggle_ui_state(True, job['id'])

                settings = self.mw.current_settings
                output_format = settings.get('output_format', 'png')

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
                    export_mode = settings.get('export_mode', 'new_safe')
                    
                    if export_mode == 'inplace':
                        final_output_path = source_path
                    else:
                        if export_mode == 'new_safe':
                            counter = 1
                            while os.path.exists(os.path.join(output_dir, final_output_folder_name)):
                                final_output_folder_name = f"{base_output_folder_name} ({counter})"
                                counter += 1
                        elif export_mode == 'new_overwrite':
                            target_path = os.path.join(output_dir, final_output_folder_name)
                            if os.path.exists(target_path):
                                try:
                                    shutil.rmtree(target_path)
                                    self.mw.log("INFO", f"Deleted existing output folder for overwrite: {target_path}")
                                except Exception as e:
                                    self.mw.log("ERROR", f"Failed to delete existing output folder: {e}")
                        
                        final_output_path = os.path.join(output_dir, final_output_folder_name)
                        os.makedirs(final_output_path, exist_ok=True)
                        
                    all_source_files = sorted([f for f in os.listdir(source_path) if f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.txt'))])

                    try:
                        processed_files = {os.path.splitext(f)[0] for f in os.listdir(final_output_path) if f.lower().endswith(f".{output_format}") or f.lower().endswith('.txt')}
                        files_to_process = [f for f in all_source_files if os.path.splitext(f)[0] not in processed_files]
                    except FileNotFoundError:
                        files_to_process = all_source_files

                if not files_to_process:
                    self.mw.log("INFO", f"All files for job '{job['name']}' seem to be processed already. Skipping to avoid errors.")
                    job['status'] = "Completed"
                    self.mw.job_queue.remove(job)
                    self.mw.history_queue.append(job)
                    if hasattr(self.mw.queue_manager, 'update_job_list_ui'):
                        self.mw.queue_manager.update_job_list_ui()
                    if hasattr(self.mw.queue_manager, 'update_history_list_ui'):
                        self.mw.queue_manager.update_history_list_ui()
                    QApplication.processEvents() 
                    continue

                self.mw.log("INFO", f"Found {len(files_to_process)} unprocessed image(s) for job '{job['name']}'.")

                success = True
                self.mw.log("PIPELINE", f"Resuming job '{job['name']}' (Sequential Stream).")
                
                final_config = self.build_final_config_for_job(job)
                final_config['is_single_file'] = os.path.isfile(source_path)
                is_verbose = settings.get("enable_verbose_output", False)
                
                success = self.mw.process_worker.run_pipeline_in_process(job, final_output_path, final_config, is_verbose, output_format, is_single_test=False)

                job['status'] = "Completed" if success else ("Stopped" if getattr(self.mw, '_stopped_by_user', False) else "Failed")

                if not success and not getattr(self.mw, '_stopped_by_user', False):
                    QTimer.singleShot(0, lambda j=job: QMessageBox.critical(self.mw, "Job Failed", f"The job '{j['name']}' failed due to a critical error.\n\nCheck the Live Log for details."))

                self.mw.job_queue.remove(job)
                self.mw.history_queue.append(job)
                self.mw.currently_processing_job_id = None
                if hasattr(self.mw.queue_manager, 'update_job_list_ui'):
                    self.mw.queue_manager.update_job_list_ui()
                if hasattr(self.mw.queue_manager, 'update_history_list_ui'):
                    self.mw.queue_manager.update_history_list_ui()

                if getattr(self.mw, '_stopped_by_user', False):
                    self.mw.log("PIPELINE", "Pipeline stopped by user command.")
                    break
        finally:
            if hasattr(self.mw, 'pipeline_finished_signal'):
                self.mw.pipeline_finished_signal.emit()

    def stop_pipeline(self):
        if not getattr(self.mw, 'is_running_pipeline', False):
            return

        self.mw.log("PIPELINE", "Stop command received. Terminating backend process...")
        self.mw._stopped_by_user = True
        
        if hasattr(self.mw, 'current_process') and self.mw.current_process and self.mw.current_process.is_alive():
            self.mw.current_process.terminate()

    def toggle_ui_state(self, is_running: bool, running_job_id: str = None):
        self.mw.is_running_pipeline = is_running
        if hasattr(self.mw, 'start_button'):
            self.mw.start_button.setEnabled(not is_running)
        if hasattr(self.mw, 'stop_button'):
            self.mw.stop_button.setEnabled(is_running)

        if hasattr(self.mw, 'queue_list_widget'):
            for i in range(self.mw.queue_list_widget.count()):
                item = self.mw.queue_list_widget.item(i)
                if is_running and item.data(Qt.ItemDataRole.UserRole) == running_job_id:
                    item.setFlags(item.flags() & ~Qt.ItemFlag.ItemIsEnabled)
                else:
                    item.setFlags(item.flags() | Qt.ItemFlag.ItemIsEnabled)

    def set_settings_panel_enabled(self, is_enabled: bool):
        interactive_widget_types = (QPushButton, QComboBox, QCheckBox, QSlider, QLineEdit)

        if hasattr(self.mw, 'settings_tab_view'):
            for widget_type in interactive_widget_types:
                for widget in self.mw.settings_tab_view.findChildren(widget_type):
                    widget.setEnabled(is_enabled)

    def update_progress(self, percent: float, text: str):
        if hasattr(self.mw, 'progress_bar'):
            self.mw.progress_bar.setValue(int(percent * 100))
        if hasattr(self.mw, 'progress_label'):
            self.mw.progress_label.setText(text)

    def on_pipeline_finished(self):
        self.mw.is_running_pipeline = False
        self.mw.currently_processing_job_id = None
        self.update_progress(1.0, "Finished!")
        QTimer.singleShot(100, lambda: self.toggle_ui_state(False))
        QTimer.singleShot(2000, lambda: self.update_progress(0, "Ready"))

    def apply_settings_to_selection(self):
        selected_items = self.mw.queue_list_widget.selectedItems()
        if not selected_items:
            return

        for item in selected_items:
            job_id = item.data(Qt.ItemDataRole.UserRole)
            job_data = next((job for job in self.mw.job_queue if job['id'] == job_id), None)
            if job_data:
                job_data['settings'] = self.mw.current_settings.copy()
                job_data['status'] = 'Ready'
                job_data['job_type'] = 'T'

        self.mw.log("INFO", f"Applied 'Translate [T]' settings to {len(selected_items)} job(s).")
        if hasattr(self.mw.queue_manager, 'update_job_list_ui'):
            self.mw.queue_manager.update_job_list_ui()
