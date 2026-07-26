"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.desktop.logic.pipeline_runner.process_worker
- RESPONSIBILITY: Run translation tasks in isolated processes.
- CALLED BY: app.core.desktop.logic.pipeline_runner.thread_manager
- CALLS TO: multiprocessing, queue
- IN = OUT: Receives pages to translate, returns translated components.
=============================================================================
"""
import time
import multiprocessing
import queue
from PySide6.QtWidgets import QApplication

def _pipeline_process_worker(job_or_path, output_path, config_dict, is_verbose, output_format, log_queue, result_queue, hitl_tx_queue, hitl_rx_queue, temp_dir, python_exec, is_single_test=False):
    from app.core.pipeline.manager import PipelineManager
    
    waiting_ctxs = {}
    
    def log_callback(level, message):
        log_queue.put((level, message))
        
    try:
        pipeline = PipelineManager(None, python_exec, temp_dir)
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

class ProcessWorker:
    def __init__(self, main_window):
        self.mw = main_window

    def run_pipeline_in_process(self, job_or_path, output_path, config_dict, is_verbose, output_format, is_single_test=False):
        log_queue = multiprocessing.Queue()
        result_queue = multiprocessing.Queue()
        hitl_tx_queue = multiprocessing.Queue()
        self.mw.hitl_rx_queue = multiprocessing.Queue()
        
        self.mw.current_process = multiprocessing.Process(
            target=_pipeline_process_worker,
            args=(job_or_path, output_path, config_dict, is_verbose, output_format, log_queue, result_queue, hitl_tx_queue, self.mw.hitl_rx_queue, self.mw.temp_dir, self.mw.config_loader.python_executable, is_single_test)
        )
        self.mw.current_process.start()
        
        success = False
        while self.mw.current_process.is_alive():
            while True:
                try:
                    level, msg = log_queue.get_nowait()
                    if msg.startswith("[TRANSLATE_WORKER]"):
                        msg = msg.replace("[TRANSLATE_WORKER]", "").strip()
                        if hasattr(self.mw, 'translator_log_signal'):
                            self.mw.translator_log_signal.emit(level, msg)
                        else:
                            self.mw.log(level, msg)
                    else:
                        self.mw.log(level, msg)
                except queue.Empty:
                    break
                    
            if getattr(self.mw, '_stopped_by_user', False):
                self.mw.current_process.terminate()
                self.mw.current_process.join()
                self.mw.log("PIPELINE", "Process terminated by user.")
                return False
                
            time.sleep(0.1)
            QApplication.processEvents()
            
        while True:
            try:
                level, msg = log_queue.get_nowait()
                if msg.startswith("[TRANSLATE_WORKER]"):
                    msg = msg.replace("[TRANSLATE_WORKER]", "").strip()
                    if hasattr(self.mw, 'translator_log_signal'):
                        self.mw.translator_log_signal.emit(level, msg)
                    else:
                        self.mw.log(level, msg)
                else:
                    self.mw.log(level, msg)
            except queue.Empty:
                break
                
        try:
            result = result_queue.get_nowait()
            success = result.get("success", False)
        except queue.Empty:
            if self.mw.current_process.exitcode != 0 and not getattr(self.mw, '_stopped_by_user', False):
                self.mw.log("ERROR", f"Process crashed unexpectedly! Exit code: {self.mw.current_process.exitcode}")
            success = False
            
        self.mw.current_process = None
        return success
