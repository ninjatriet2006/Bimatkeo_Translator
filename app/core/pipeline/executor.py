"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.executor
- RESPONSIBILITY: Runs the multi-process Fork-Join pipeline execution logic.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.ocr.ocr.OCRWorker, app.core.translator.translate.TranslateWorker, etc.
- IN = OUT: Receives config_dict, starts processes, runs produce/consume.
=============================================================================
"""

import os
import queue
import multiprocessing
import threading

from app.core.pipeline.producer import produce
from app.core.pipeline.consumer import consume

from app.core.ocr.ocr import OCRWorker
from app.core.translator.translate import TranslateWorker
from app.core.translator.edit import EditWorker
from app.core.inpainter.inpaint import InpaintWorker
from app.core.inpainter.upscale import UpscalerWorker
from app.core.renderer.render import RenderWorker

def _log_listener(log_queue: multiprocessing.Queue, log_callback):
    """Listens for logs from child processes and forwards them to the main UI."""
    while True:
        try:
            msg = log_queue.get()
            if msg is None:
                break
            level, text = msg
            if log_callback:
                log_callback(level, text)
        except EOFError:
            break

class PipelineExecutor:
    """Handles the execution of the backend translation process via Multi-process Fork-Join Queue Architecture."""

    def __init__(self, app, python_executable, temp_dir):
        self.app = app
        self.python_executable = python_executable
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self._stopped_by_user = False

    def is_stopped(self):
        return self._stopped_by_user

    def stop(self, log_callback):
        """Stops the pipeline execution."""
        self._stopped_by_user = True
        if log_callback:
            log_callback("PIPELINE", "msg_pipeline_stopped")
        return True

    def run(self, job, output_path, config_dict, log_callback, is_verbose=False, output_format='png', mtpe_callback=None):
        """Runs the real multi-process pipeline."""
        source_path = job['source_path']
        job_name = os.path.basename(source_path)
        log_callback("PIPELINE", f"msg_pipeline_starting|job_name={job_name}")
        self._stopped_by_user = False

        if os.path.isfile(source_path):
            source_dir = os.path.dirname(source_path)
            all_files = [os.path.basename(source_path)]
        else:
            source_dir = source_path
            is_single_file = config_dict.get('is_single_file', False)
            all_files = sorted([
                f for f in os.listdir(source_path) 
                if is_single_file or f.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.bmp', '.txt'))
            ])

        if not all_files:
            log_callback("WARNING", "msg_pipeline_no_files")
            return True

        target_lang = config_dict.get("translator", {}).get("target_lang", "VIN")

        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Initialize multiprocessing Queues
            q_in = multiprocessing.Queue()
            q_trans = multiprocessing.Queue()
            q_edit = multiprocessing.Queue()
            q_inpaint = multiprocessing.Queue()
            q_upscale = multiprocessing.Queue()
            
            q_trans_done = multiprocessing.Queue()
            q_inpaint_done = multiprocessing.Queue()
            
            q_out = multiprocessing.Queue()
            
            log_queue = multiprocessing.Queue()
            
            # Start log listener thread
            log_thread = threading.Thread(target=_log_listener, args=(log_queue, log_callback), daemon=True)
            log_thread.start()

            # Create Process Workers (Pass config_dict instead of initialized models)
            ocr_worker = OCRWorker(
                in_q=q_in, out_q_trans=q_trans, out_q_inpaint=q_inpaint,
                config_dict=config_dict, log_queue=log_queue
            )
            
            trans_worker = TranslateWorker(
                in_q=q_trans,
                out_q=q_edit if config_dict.get("translator", {}).get("use_editor", False) else q_trans_done,
                config_dict=config_dict,
                log_queue=log_queue
            )
            
            edit_worker = None
            if config_dict.get("translator", {}).get("use_editor", False):
                edit_worker = EditWorker(
                    in_q=q_edit,
                    out_q=q_trans_done,
                    config_dict=config_dict,
                    log_queue=log_queue
                )
            
            enable_upscaler = config_dict.get("inpainter", {}).get("upscale", False)
            inpaint_worker = InpaintWorker(
                in_q=q_inpaint, 
                out_q=q_upscale if enable_upscaler else q_inpaint_done,
                config_dict=config_dict,
                log_queue=log_queue
            )
            
            upscale_worker = None
            if enable_upscaler:
                upscale_worker = UpscalerWorker(
                    in_q=q_upscale, 
                    out_q=q_inpaint_done,
                    config_dict=config_dict,
                    log_queue=log_queue
                )
                
            render_worker = RenderWorker(
                q_trans_done=q_trans_done, q_inpaint_done=q_inpaint_done, out_q=q_out, 
                config_dict=config_dict,
                log_queue=log_queue
            )

            # Start Workers
            workers: list[multiprocessing.Process] = [ocr_worker, trans_worker, inpaint_worker, render_worker]
            if edit_worker:
                workers.append(edit_worker)
            if upscale_worker:
                workers.append(upscale_worker)
            
            for w in workers:
                w.start()

            # Produce Input
            produce(
                all_files=all_files,
                source_dir=source_dir,
                output_path=output_path,
                config_dict=config_dict,
                log_callback=log_callback,  # Producer runs in main process, can use standard callback
                q_in=q_in,
                stop_check_callback=self.is_stopped
            )

            # Consume Output
            consume(
                output_path=output_path,
                config_dict=config_dict,
                log_callback=log_callback,
                q_out=q_out
            )

            # Wait for processes
            for w in workers:
                w.join()

            # Stop logger
            log_queue.put(None)
            log_thread.join()

            if self._stopped_by_user:
                log_callback("WARNING", "msg_pipeline_stopped")
                return False

            log_callback("PIPELINE", f"msg_pipeline_completed|job_name={job_name}")
            return True
            
        except Exception as e:
            log_callback("ERROR", f"msg_pipeline_error|error={e}")
            import traceback
            traceback.print_exc()
            return False

    def run_single_image_test(self, test_image_path, output_path, config_dict, log_callback, is_verbose=False):
        job_dict = {
            'source_path': test_image_path,
            'job_type': config_dict.get('job_type', 'T')
        }
        config_dict['is_single_file'] = True
        return self.run(job_dict, output_path, config_dict, log_callback, is_verbose, output_format='png')
