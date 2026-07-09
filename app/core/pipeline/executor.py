"""
=============================================================================
INTEGRITY NOTES (For AI Agents):
- MODULE: app.core.pipeline.executor
- RESPONSIBILITY: Runs the multi-threaded Fork-Join pipeline execution logic.
- CALLED BY: app.core.pipeline.manager
- CALLS TO: app.core.ocr.ocr.OCRWorker, app.core.translator.translate.TranslateWorker, etc.
- IN = OUT: Receives initialized models, starts threads, runs produce/consume.
=============================================================================
"""

import os
import queue
import threading

from app.core.pipeline.producer import produce
from app.core.pipeline.consumer import consume

from app.core.ocr.ocr import OCRWorker
from app.core.translator.translate import TranslateWorker
from app.core.translator.edit import EditWorker
from app.core.inpainter.inpaint import InpaintWorker
from app.core.inpainter.upscale import UpscalerWorker
from app.core.renderer.render import RenderWorker

class PipelineExecutor:
    """Handles the execution of the backend translation process via Fork-Join Queue Architecture."""

    def __init__(self, app, python_executable, temp_dir):
        self.app = app
        self.python_executable = python_executable
        self.temp_dir = temp_dir
        os.makedirs(self.temp_dir, exist_ok=True)
        self.process = None
        self._stopped_by_user = False

    def is_stopped(self):
        return self._stopped_by_user

    def stop(self, log_callback):
        """Stops the pipeline simulation."""
        self._stopped_by_user = True
        if log_callback:
            log_callback("PIPELINE", "Pipeline stopped by user.")
        return True

    def run(self, job, output_path, config_dict, log_callback, models_bundle, is_verbose=False, output_format='png', mtpe_callback=None):
        """Runs the real multi-threaded pipeline."""
        source_path = job['source_path']
        log_callback("PIPELINE", f"Starting Modular Pipeline for job '{os.path.basename(source_path)}'.")
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
            log_callback("WARNING", "No files found in the source directory.")
            return True

        # Unpack models
        cloud_ocr, detector, recognizer = models_bundle.get("ocr", (None, None, None))
        chained_translators, editor_translator = models_bundle.get("translator", ([], None))
        inpainter, upscaler, enable_upscaler, upscale_ratio = models_bundle.get("inpainter", (None, None, False, 2))
        renderer = models_bundle.get("renderer", None)

        target_lang = config_dict.get("translator", {}).get("target_lang", "VIN")
        skip_languages = config_dict.get("skip_languages", {})
        filter_texts = config_dict.get("filter_texts", [])

        try:
            os.makedirs(output_path, exist_ok=True)
            
            # Initialize Queues for Fork-Join
            q_in = queue.Queue()
            q_trans = queue.Queue()
            q_edit = queue.Queue()
            q_inpaint = queue.Queue()
            q_upscale = queue.Queue()
            q_render = queue.Queue()
            q_out = queue.Queue()

            # Create Workers
            ocr_worker = OCRWorker(
                in_q=q_in, out_q_trans=q_trans, out_q_inpaint=q_inpaint, out_q_render=q_render,
                detector=detector, recognizer=recognizer, log_callback=log_callback,
                cloud_ocr=cloud_ocr, ocr_config=config_dict.get("ocr", {}), render_config=config_dict.get("render", {})
            )
            
            trans_worker = TranslateWorker(
                in_q=q_trans,
                out_q=q_edit if editor_translator else None,
                translator_or_chain=chained_translators, 
                src_lang=config_dict.get("translator", {}).get("source_lang", "JPN"), 
                tgt_lang=target_lang,
                log_callback=log_callback,
                skip_languages=skip_languages,
                filter_texts=filter_texts,
                no_text_lang_skip=config_dict.get("translator", {}).get("no_text_lang_skip", False),
                max_request_length=int(config_dict.get("translator", {}).get("max_request_length", 2000)),
                context_window=int(config_dict.get("translator", {}).get("context_window", 10)),
                stride_window=int(config_dict.get("translator", {}).get("stride_window", 5))
            )
            
            edit_worker = EditWorker(
                in_q=q_edit,
                editor_translator=editor_translator,
                log_callback=log_callback,
                max_request_length=int(config_dict.get("translator", {}).get("max_request_length", 2000)),
                context_window=int(config_dict.get("translator", {}).get("context_window", 10)),
                stride_window=int(config_dict.get("translator", {}).get("stride_window", 5))
            ) if editor_translator else None
            
            inpaint_worker = InpaintWorker(q_inpaint, inpainter, log_callback, out_q=q_upscale if enable_upscaler else None)
            upscale_worker = UpscalerWorker(q_upscale, upscaler, upscale_ratio, log_callback) if enable_upscaler else None
            render_worker = RenderWorker(q_render, q_out, renderer, log_callback)

            # Start Workers
            workers: list[threading.Thread] = [ocr_worker, trans_worker, inpaint_worker, render_worker]
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
                log_callback=log_callback,
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

            # Wait for all queues to empty
            join_workers: list[threading.Thread] = [ocr_worker, trans_worker, inpaint_worker, render_worker]
            if edit_worker:
                join_workers.append(edit_worker)
            if upscale_worker:
                join_workers.append(upscale_worker)
            for w in join_workers:
                w.join()

            if self._stopped_by_user:
                log_callback("WARNING", "Pipeline run stopped by user.")
                return False

            log_callback("PIPELINE", f"Job '{os.path.basename(source_path)}' completed successfully.")
            return True
            
        except Exception as e:
            log_callback("ERROR", f"Error executing pipeline: {e}")
            import traceback
            traceback.print_exc()
            return False

    def run_single_image_test(self, test_image_path, output_path, config_dict, log_callback, models_bundle, is_verbose=False):
        job_dict = {
            'source_path': test_image_path,
            'job_type': config_dict.get('job_type', 'T')
        }
        config_dict['is_single_file'] = True
        return self.run(job_dict, output_path, config_dict, log_callback, models_bundle, is_verbose, output_format='png')
